"""Main test runner for conversational layer tests.

Orchestrates test execution, judge evaluation, interrogation, and results collection.
"""

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .errors import flush_output, handle_subprocess_error
from .fixtures import (
    clean_graph_state,
    extract_text,
    parse_payload,
    setup_graph_from_fixture,
)
from .interrogation import interrogate_session, QAPair, format_interrogation_for_json
from .judge import run_judge, Verdict
from .logging_config import get_logger, log_test_start, log_test_result
from .models import TestResult, TestSuiteResults
from .retry import retry_with_backoff
from .user_proxy import (
    UserProxy,
    LLMUserProxy,
    is_conversational_test,
    extract_conversational_config,
)
from .results_db import ResultsDB


CLAUDE_CMD = "claude"
MCP_LOG_PATH = Path("/Users/scottmcguire/Share1/Projects/personal-assistant-gtd-style/.data/gtd-memory/mcp-calls.log")


def clear_mcp_log() -> None:
    """Clear MCP call log file before test execution."""
    try:
        if MCP_LOG_PATH.exists():
            MCP_LOG_PATH.unlink()
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Failed to clear MCP log: {e}")


def read_mcp_log() -> str:
    """Read MCP call log file after test execution.

    Returns:
        String content of MCP log file, or empty string if not found
    """
    try:
        if MCP_LOG_PATH.exists():
            return MCP_LOG_PATH.read_text(encoding='utf-8')
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Failed to read MCP log: {e}")

    return ""


def run_claude_assistant(
    system_prompt_path: Optional[Path],
    append_prompts: List[str],
    user_prompt: str,
    mcp_config_path: Optional[Path],
    timeout: float
) -> subprocess.CompletedProcess[str]:
    """Execute Claude CLI for assistant.

    Args:
        system_prompt_path: Path to system prompt file
        append_prompts: List of prompts to append
        user_prompt: User's prompt
        mcp_config_path: Optional MCP config
        timeout: Timeout in seconds

    Returns:
        CompletedProcess with stdout/stderr
    """
    args = [CLAUDE_CMD]
    if mcp_config_path:
        args += ["--mcp-config", str(mcp_config_path)]
    args += ["--model", "sonnet", "--dangerously-skip-permissions", "--print", "--output-format", "json"]

    if system_prompt_path and system_prompt_path.exists():
        args += ["--system-prompt", str(system_prompt_path)]

    for append_content in append_prompts:
        if append_content.strip():
            args += ["--append-system-prompt", append_content]

    args.append(user_prompt)

    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def run_assistant_single_attempt(
    case: Dict[str, Any],
    config: Config,
    append_prompts: List[str]
) -> Dict[str, Any]:
    """Run assistant for single attempt (no retry).

    Args:
        case: Test case dictionary
        config: Test configuration
        append_prompts: System prompt additions

    Returns:
        Result dictionary with pass/assistant/full_output/mcp_logs/session_id
    """
    logger = get_logger()

    # Clear MCP log before execution
    clear_mcp_log()

    try:
        result = run_claude_assistant(
            config.system_prompt_path,
            append_prompts,
            case["prompt"],
            config.mcp_config_path,
            config.assistant_timeout
        )

        # Read MCP logs after execution
        mcp_logs = read_mcp_log()

        if result.returncode != 0:
            reason = result.stderr.strip() or "Assistant CLI error"
            logger.warning(f"Assistant CLI error: {reason}")
            return {
                "pass": False,
                "assistant": "",
                "full_output": "",
                "mcp_logs": mcp_logs,
                "reason": reason,
                "retry": True
            }

        payload = parse_payload(result.stdout)
        if payload is None:
            logger.warning("Assistant returned non-JSON output")
            return {
                "pass": False,
                "assistant": result.stdout.strip(),
                "full_output": result.stdout.strip(),
                "mcp_logs": mcp_logs,
                "reason": "Assistant returned non-JSON output",
                "retry": True
            }

        session_id = payload.get("session_id", "")
        assistant_text = extract_text(payload).strip()

        # Combine stdout and MCP logs in full_output
        full_output = result.stdout.strip()
        if mcp_logs:
            full_output += "\n\n=== MCP Tool Calls ===\n" + mcp_logs

        return {
            "pass": True,
            "assistant": assistant_text,
            "full_output": full_output,
            "mcp_logs": mcp_logs,
            "session_id": session_id,
            "retry": False
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Assistant timeout after {config.assistant_timeout}s")
        mcp_logs = read_mcp_log()
        return {
            "pass": False,
            "assistant": "",
            "full_output": "",
            "mcp_logs": mcp_logs,
            "reason": f"Assistant timeout ({config.assistant_timeout}s)",
            "retry": True
        }
    except Exception as e:
        mcp_logs = read_mcp_log()
        error_dict = handle_subprocess_error(e, "run_assistant")
        error_dict["mcp_logs"] = mcp_logs
        return error_dict


def run_assistant(
    case: Dict[str, Any],
    config: Config,
    append_prompts: List[str]
) -> Dict[str, Any]:
    """Run assistant with retry logic.

    Args:
        case: Test case dictionary
        config: Test configuration
        append_prompts: System prompt additions

    Returns:
        Result dictionary
    """
    return retry_with_backoff(
        run_assistant_single_attempt,
        max_retries=config.max_retries,
        initial_backoff=config.initial_backoff,
        case=case,
        config=config,
        append_prompts=append_prompts
    )


def run_single_test(
    case: Dict[str, Any],
    config: Config,
    append_prompts: List[str],
    run_number: int
) -> TestResult:
    """Run a single test case.

    Args:
        case: Test case dictionary
        config: Test configuration
        append_prompts: System prompt additions
        run_number: Which run this is (1-based)

    Returns:
        TestResult object
    """
    logger = get_logger()
    start_time = time.time()

    expected_pass = bool(case.get("expected_pass", True))
    session_id = None

    # Set up graph fixture if specified
    if case.get("graph_setup") and config.is_live_mcp_mode() and "assistant_override" not in case:
        logger.info(f"Setting up graph fixture for {case['name']}")
        if not setup_graph_from_fixture(case["graph_setup"], config):
            logger.warning(f"Graph setup failed for {case['name']}")

    # Run assistant (or use override for negative controls)
    if "assistant_override" in case:
        assistant_result = {
            "pass": True,
            "assistant": case["assistant_override"],
            "full_output": case["assistant_override"],
            "session_id": ""
        }
    elif is_conversational_test(case):
        # Multi-turn conversation with LLM user-proxy
        logger.info(f"Running conversational test: {case['name']}")

        # Clear MCP log before conversation
        clear_mcp_log()

        conv_config = extract_conversational_config(case)
        user_proxy = LLMUserProxy(config)

        conv_result = user_proxy.run_conversation(
            initial_prompt=case["prompt"],
            conv_config=conv_config,
            append_prompts=append_prompts,
            case_name=case["name"],
            case=case
        )

        # Read MCP logs after conversation completes
        mcp_logs = read_mcp_log()

        # Convert ConversationResult to assistant_result format
        if conv_result.success:
            # Combine transcript and MCP logs
            full_output = conv_result.full_transcript
            if mcp_logs:
                full_output += "\n\n=== MCP Tool Calls ===\n" + mcp_logs

            assistant_result = {
                "pass": True,
                "assistant": conv_result.final_response,
                "full_output": full_output,
                "mcp_logs": mcp_logs,
                "session_id": conv_result.session_id
            }
        else:
            assistant_result = {
                "pass": False,
                "assistant": "",
                "full_output": "",
                "mcp_logs": mcp_logs,
                "reason": conv_result.reason,
                "session_id": conv_result.session_id
            }

        session_id = conv_result.session_id
    else:
        # Single-turn test
        assistant_result = run_assistant(case, config, append_prompts)
        session_id = assistant_result.get("session_id")

    # Check if assistant failed
    if not assistant_result["pass"]:
        duration = time.time() - start_time
        return TestResult(
            test_name=case["name"],
            category=case["category"],
            run_number=run_number,
            passed=False,
            expected_pass=expected_pass,
            actual_pass=False,
            reason=assistant_result.get("reason", "Unknown error"),
            duration=duration,
            session_id=session_id or ""
        )

    # Extract responses
    assistant_text = assistant_result["assistant"]
    full_output = assistant_result.get("full_output", assistant_text)

    # Run judge
    judge_result = run_judge(case, assistant_text, full_output, config)
    actual_pass = bool(judge_result.get("pass"))
    verdict = judge_result.get("verdict")

    # Determine if test passed overall
    test_passed = (actual_pass == expected_pass)

    # Interrogation if configured
    interrogation_qa = None
    if session_id and config.should_interrogate(actual_pass):
        logger.info(f"Interrogating {case['name']}")
        # Pass verdict dict to interrogation so it can include judge feedback in Q2
        verdict_dict = verdict.to_dict() if verdict else None
        interrogation_qa = interrogate_session(session_id, actual_pass, config, case["name"], verdict=verdict_dict)

    duration = time.time() - start_time

    return TestResult(
        test_name=case["name"],
        category=case["category"],
        run_number=run_number,
        passed=test_passed,
        expected_pass=expected_pass,
        actual_pass=actual_pass,
        reason=judge_result.get("reason", ""),
        verdict=verdict,
        assistant_response=assistant_text,
        full_transcript=full_output,
        interrogation=interrogation_qa,
        duration=duration,
        session_id=session_id or ""
    )


def load_test_cases(config: Config) -> List[Dict[str, Any]]:
    """Load test cases from JSON file.

    Args:
        config: Test configuration

    Returns:
        List of test case dictionaries
    """
    with open(config.test_cases_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Test cases file must contain a list")

    return data


def filter_test_cases(
    cases: List[Dict[str, Any]],
    config: Config
) -> List[Dict[str, Any]]:
    """Filter test cases based on configuration.

    Args:
        cases: All test cases
        config: Test configuration

    Returns:
        Filtered list of test cases
    """
    filtered = cases

    # Filter by category
    if config.category:
        filtered = [c for c in filtered if c.get("category") == config.category]

    # Filter by test name
    if config.test_name:
        filtered = [c for c in filtered if c.get("name") == config.test_name]

    # Filter by suite (assistant vs judge negative controls)
    if config.suite == "assistant":
        # Exclude judge negative controls
        filtered = [c for c in filtered if not c.get("name", "").startswith("judge_")]
    elif config.suite == "judge":
        # Only judge negative controls
        filtered = [c for c in filtered if c.get("name", "").startswith("judge_")]

    return filtered


def build_append_prompts(config: Config) -> List[str]:
    """Build list of system prompt additions for test mode.

    Args:
        config: Test configuration

    Returns:
        List of prompt strings to append
    """
    overlays = config.get_test_overlays()
    append_prompts = []

    for overlay_path in overlays:
        if overlay_path.exists():
            content = overlay_path.read_text(encoding='utf-8').strip()
            if content:
                append_prompts.append(content)

    return append_prompts


def run_test_suite(config: Config) -> TestSuiteResults:
    """Run complete test suite with N runs.

    Args:
        config: Test configuration

    Returns:
        TestSuiteResults with aggregated results
    """
    logger = get_logger()
    suite_start = time.time()

    logger.info(f"Starting test suite in {config.mode} mode")
    logger.info(f"Runs: {config.runs}, Inter-run delay: {config.inter_run_delay}s")

    # Load and filter test cases
    all_cases = load_test_cases(config)
    selected_cases = filter_test_cases(all_cases, config)

    if not selected_cases:
        logger.warning("No test cases matched filters")
        return TestSuiteResults()

    logger.info(f"Selected {len(selected_cases)} test cases")

    # Build append prompts (test overlays)
    append_prompts = build_append_prompts(config)

    # Initialize results database
    db: Optional[ResultsDB] = None
    run_id: Optional[int] = None
    try:
        db = ResultsDB(config.results_db)
        logger.info(f"Initialized results database: {config.results_db}")

        # Create run record (we'll populate counts later)
        # Create a preliminary suite_results for run creation
        preliminary_results = TestSuiteResults(
            total=len(selected_cases) * config.runs,
            passed=0,
            failed=0,
            results=[],
            interrogations=0,
            duration=0.0
        )
        run_id = db.create_run(config, preliminary_results)
        logger.info(f"Created run record: run_id={run_id}")
    except Exception as e:
        logger.warning(f"Failed to initialize database: {e}")
        db = None

    # Initial graph cleanup if requested
    if config.should_clean_graph():
        logger.info("Performing initial graph cleanup")
        if not clean_graph_state(config):
            logger.warning("Initial graph cleanup failed, continuing anyway")

    # Run tests N times
    all_results = []

    for run_num in range(1, config.runs + 1):
        if config.runs > 1:
            logger.info(f"=== Run {run_num}/{config.runs} ===")

        for index, case in enumerate(selected_cases, start=1):
            log_test_start(logger, case["name"], run_num, config.runs)

            # Run test
            result = run_single_test(case, config, append_prompts, run_num)
            all_results.append(result)

            # Save to database incrementally (if run_id created)
            if db and run_id:
                try:
                    db.save_test_result(run_id, result)
                except Exception as e:
                    logger.warning(f"Failed to save test result to DB: {e}")

            # Log result
            log_test_result(
                logger,
                case["name"],
                result.passed,
                result.reason if not result.passed else None,
                result.duration
            )

            # Flush output
            flush_output()

            # Inter-test delay (except after last test)
            if config.inter_test_delay > 0 and index < len(selected_cases):
                time.sleep(config.inter_test_delay)

            # Clean graph between tests if requested
            if config.should_clean_graph() and index < len(selected_cases):
                logger.debug("Cleaning graph before next test")
                if not clean_graph_state(config):
                    logger.warning("Graph cleanup failed between tests")

        # Inter-run delay (except after last run)
        if run_num < config.runs:
            logger.info(f"Run {run_num} complete, waiting {config.inter_run_delay}s...")
            time.sleep(config.inter_run_delay)

    # Aggregate results
    suite_duration = time.time() - suite_start
    passed_count = sum(1 for r in all_results if r.passed)
    interrogations_count = sum(1 for r in all_results if r.interrogation)

    suite_results = TestSuiteResults(
        total=len(all_results),
        passed=passed_count,
        failed=len(all_results) - passed_count,
        results=all_results,
        interrogations=interrogations_count,
        duration=suite_duration
    )

    logger.info(f"Test suite complete: {passed_count}/{len(all_results)} passed")
    logger.info(f"Total duration: {suite_duration:.1f}s")

    # Update run record with final counts
    if db and run_id:
        try:
            cursor = db.conn.cursor()
            cursor.execute("""
                UPDATE runs
                SET passed_count = ?, failed_count = ?, duration = ?
                WHERE run_id = ?
            """, (suite_results.passed, suite_results.failed, suite_results.duration, run_id))
            db.conn.commit()
            logger.info(f"Updated run record with final counts")
        except Exception as e:
            logger.warning(f"Failed to update run record: {e}")

    # Close database
    if db:
        try:
            db.close()
            logger.debug("Closed results database")
        except Exception as e:
            logger.warning(f"Failed to close database: {e}")

    return suite_results


def print_suite_summary(results: TestSuiteResults, config: Config):
    """Print test suite summary to console.

    Args:
        results: Test suite results
        config: Test configuration
    """
    print(f"\n{'='*70}")
    print(f"TEST SUITE SUMMARY")
    print(f"{'='*70}")
    print(f"Mode: {config.mode}")
    print(f"Total tests: {results.total}")
    print(f"Passed: {results.passed} ({100*results.passed/results.total if results.total > 0 else 0:.1f}%)")
    print(f"Failed: {results.failed}")
    print(f"Duration: {results.duration:.1f}s")

    if results.interrogations > 0:
        print(f"Interrogations: {results.interrogations}")

    # Group by category
    by_category: Dict[str, List[TestResult]] = {}
    for result in results.results:
        if result.category not in by_category:
            by_category[result.category] = []
        by_category[result.category].append(result)

    print(f"\nBy Category:")
    for category, cat_results in sorted(by_category.items()):
        cat_passed = sum(1 for r in cat_results if r.passed)
        cat_total = len(cat_results)
        print(f"  {category}: {cat_passed}/{cat_total} ({100*cat_passed/cat_total:.1f}%)")

    # Show failures
    failures = [r for r in results.results if not r.passed]
    if failures:
        print(f"\nFailed Tests:")
        for failure in failures[:20]:  # Limit to first 20
            print(f"  - {failure.test_name} (run {failure.run_number}): {failure.reason[:100]}")

        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more")
