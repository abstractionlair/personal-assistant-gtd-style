"""
Markdown Test Report Generator

Generates comprehensive human-readable Markdown reports from test run results.
Supports multi-run aggregation with per-test statistics and detailed transcripts.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

from .results_db import ResultsDB
from .logging_config import get_logger


def generate_markdown_report(
    db: ResultsDB,
    run_id: int,
    output_path: Optional[str] = None,
    test_cases_path: Path = Path("tests/test_cases_refactored.json")
) -> Path:
    """
    Generate comprehensive Markdown report from test run.

    Args:
        db: ResultsDB instance with test results
        run_id: ID of the test run to report on
        output_path: Optional custom output path
        test_cases_path: Path to test cases JSON file

    Returns:
        Path to generated report file

    Raises:
        FileNotFoundError: If test cases file not found
        ValueError: If run_id not found in database
    """
    logger = get_logger()
    logger.info(f"Generating Markdown report for run_id={run_id}")

    # Load test cases for prompts
    test_cases = _load_test_cases(test_cases_path)

    # Query database
    run_summary = db.get_run_summary(run_id)
    if not run_summary:
        raise ValueError(f"Run ID {run_id} not found in database")

    test_results = db.get_test_results(run_id)
    category_stats = db.get_category_stats(run_id)
    flaky_tests = db.get_flaky_tests(min_runs=5, instability_threshold=0.3)

    # Determine output path
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"tests/report_{run_id}_{timestamp}.md"

    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate report sections
    sections = []
    sections.append(_format_header(run_summary))
    sections.append(_format_overall_stats(run_summary, test_results, flaky_tests))
    sections.append(_format_categories(test_results, category_stats, test_cases, db))

    # Write report
    content = "\n\n".join(sections)
    report_path.write_text(content)

    logger.info(f"Markdown report saved to: {report_path}")
    return report_path


def _load_test_cases(path: Path) -> Dict[str, Dict]:
    """Load test cases from JSON file and index by name."""
    if not path.exists():
        raise FileNotFoundError(f"Test cases file not found: {path}")

    with open(path) as f:
        test_list = json.load(f)

    return {test["name"]: test for test in test_list}


def _format_header(run_summary: Dict) -> str:
    """Format report header with timestamp and metadata."""
    timestamp = run_summary.get("timestamp", "Unknown")
    # Parse ISO timestamp
    try:
        dt = datetime.fromisoformat(timestamp)
        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        formatted_date = timestamp

    return f"# Test Run Report\n\n**Run ID:** {run_summary['run_id']}  \n**Date:** {formatted_date}  \n**Duration:** {run_summary['duration']:.1f}s"


def _format_overall_stats(
    run_summary: Dict,
    test_results: List[Dict],
    flaky_tests: List[Dict]
) -> str:
    """Format overall statistics section."""
    lines = ["## Overall Statistics"]

    total_tests = run_summary.get("test_count", 0)
    passed = run_summary.get("passed_count", 0)
    failed = run_summary.get("failed_count", 0)
    runs_count = run_summary.get("runs_count", 1)

    pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0

    # Determine unique test names from test results
    unique_tests = set()
    for result in test_results:
        unique_tests.add(result.get("test_name"))
    num_unique_tests = len(unique_tests)

    lines.append(f"- **Total unique tests:** {num_unique_tests}")
    lines.append(f"- **Total runs:** {total_tests} ({runs_count} run{'s' if runs_count != 1 else ''} per test)")
    lines.append(f"- **Passed:** {passed}/{total_tests} ({pass_rate:.1f}%)")
    lines.append(f"- **Failed:** {failed}/{total_tests}")

    # Flaky tests
    flaky_count = len(flaky_tests)
    if flaky_count > 0:
        lines.append(f"- **Flaky tests:** {flaky_count}")
        for flaky in flaky_tests:
            test_name = flaky.get("test_name", "Unknown")
            pass_count = flaky.get("pass_count", 0)
            total_runs = flaky.get("total_runs", 0)
            flaky_rate = (pass_count / total_runs * 100) if total_runs > 0 else 0
            lines.append(f"  - `{test_name}`: {pass_count}/{total_runs} ({flaky_rate:.1f}%)")
    else:
        lines.append(f"- **Flaky tests:** None detected")

    return "\n".join(lines)


def _format_categories(
    test_results: List[Dict],
    category_stats: List[Dict],
    test_cases: Dict[str, Dict],
    db: ResultsDB
) -> str:
    """Format all category sections with tests and runs."""
    # Group test results by category
    by_category = defaultdict(list)
    for result in test_results:
        category = result.get("category", "Uncategorized")
        by_category[category].append(result)

    # Sort categories
    category_order = ["Capture", "Query", "Update", "Delete", "Edge", "NegativeControl"]
    sorted_categories = []
    for cat in category_order:
        if cat in by_category:
            sorted_categories.append(cat)
    # Add any remaining categories
    for cat in sorted(by_category.keys()):
        if cat not in sorted_categories:
            sorted_categories.append(cat)

    sections = []
    for category in sorted_categories:
        results = by_category[category]
        section = _format_category_section(category, results, test_cases, db)
        sections.append(section)

    return "\n\n".join(sections)


def _format_category_section(
    category: str,
    test_results: List[Dict],
    test_cases: Dict[str, Dict],
    db: ResultsDB
) -> str:
    """Format single category section with statistics and tests."""
    lines = [f"## Category: {category}"]

    # Calculate category statistics
    total_runs = len(test_results)
    passed_runs = sum(1 for r in test_results if r.get("passed"))
    pass_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 0

    # Count unique tests
    unique_tests = set(r.get("test_name") for r in test_results)
    num_tests = len(unique_tests)

    lines.append(f"**Tests:** {num_tests} | **Total runs:** {total_runs} | **Pass rate:** {pass_rate:.1f}%")
    lines.append("")

    # Group by test name
    by_test = defaultdict(list)
    for result in test_results:
        test_name = result.get("test_name")
        by_test[test_name].append(result)

    # Format each test
    for test_name in sorted(by_test.keys()):
        runs = by_test[test_name]
        test_section = _format_test_section(test_name, runs, test_cases, db)
        lines.append(test_section)

    return "\n".join(lines)


def _format_test_section(
    test_name: str,
    runs: List[Dict],
    test_cases: Dict[str, Dict],
    db: ResultsDB
) -> str:
    """Format single test section with aggregate stats and individual runs (collapsible)."""
    # Aggregate statistics
    total_runs = len(runs)
    passed_runs = sum(1 for r in runs if r.get("passed"))
    pass_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 0

    # Status emoji for summary
    status_emoji = "✅" if passed_runs == total_runs else "⚠️" if passed_runs > 0 else "❌"

    # Get prompt from test cases
    test_case = test_cases.get(test_name, {})
    prompt = test_case.get("prompt", "*Prompt not found*")

    # Sort runs by run_number
    sorted_runs = sorted(runs, key=lambda r: r.get("run_number", 0))

    # Create collapsible section
    lines = [
        f"<details>",
        f"<summary><strong>### Test: <code>{test_name}</code> {status_emoji}</strong> — Pass rate: {passed_runs}/{total_runs} ({pass_rate:.1f}%)</summary>",
        f"",
        f"**Initial Prompt:**",
        f"> {prompt}",
        f""
    ]

    # Format each run
    for run in sorted_runs:
        run_section = _format_run_details(run, db)
        lines.append(run_section)

    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


def _format_run_details(run: Dict, db: ResultsDB) -> str:
    """Format individual run details: transcript, verdict, interrogation (collapsible)."""
    result_id = run.get("result_id")
    run_number = run.get("run_number", 1)
    passed = run.get("passed")
    duration = run.get("duration", 0)

    status = "✅ PASS" if passed else "❌ FAIL"

    # Verdict summary for collapsed view
    verdict = _get_verdict_for_result(db, result_id)
    verdict_summary = ""
    if verdict:
        effective = verdict.get("effective", False)
        safe = verdict.get("safe", False)
        clear = verdict.get("clear", False)
        verdict_summary = f" | E:{'✓' if effective else '✗'} S:{'✓' if safe else '✗'} C:{'✓' if clear else '✗'}"

    # Create collapsible section with summary
    lines = [
        f"<details>",
        f"<summary><strong>Run {run_number}: {status}</strong> | Duration: {duration:.1f}s{verdict_summary}</summary>",
        f""
    ]

    # Transcript
    transcript_json = run.get("full_transcript")
    if transcript_json:
        lines.append("**Transcript:**")
        lines.append(_format_transcript(transcript_json))
        lines.append("")

    # Verdict (detailed)
    if verdict:
        lines.append("**Judge Verdict:**")
        lines.append(_format_verdict(verdict, passed))
        lines.append("")

    # Interrogation
    qa_pairs = _get_interrogations_for_result(db, result_id)
    if qa_pairs:
        lines.append("**Interrogation:**")
        lines.append(_format_interrogation(qa_pairs))
        lines.append("")

    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


def _format_transcript(transcript_json: str) -> str:
    """Format transcript with embedded JSON pretty-printed for readability."""
    import re

    # First try: is the entire transcript a JSON object?
    try:
        transcript_obj = json.loads(transcript_json)
        pretty_json = json.dumps(
            transcript_obj,
            indent=2,
            ensure_ascii=False,
            sort_keys=False
        )
        return f"```json\n{pretty_json}\n```"
    except (json.JSONDecodeError, TypeError):
        pass

    # Second try: transcript is text with embedded JSON (common format)
    # Format: [Turn N - User]\ntext\n\n[Turn N - Assistant]\n{json}
    lines = transcript_json.split('\n')
    formatted_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line looks like it contains JSON
        if line.strip().startswith('{'):
            # Try to parse as JSON
            try:
                json_obj = json.loads(line.strip())
                # Format it nicely
                pretty = json.dumps(json_obj, indent=2, ensure_ascii=False, sort_keys=False)
                # Indent each line for better readability
                indented = '\n'.join('  ' + l for l in pretty.split('\n'))
                formatted_lines.append(indented)
            except (json.JSONDecodeError, TypeError):
                # Not valid JSON, keep as-is
                formatted_lines.append(line)
        else:
            # Regular text line
            formatted_lines.append(line)

        i += 1

    return f"```\n" + '\n'.join(formatted_lines) + f"\n```"


def _format_verdict(verdict: Dict, passed: bool) -> str:
    """Format judge verdict with three dimensions."""
    lines = []

    effective = verdict.get("effective", False)
    safe = verdict.get("safe", False)
    clear = verdict.get("clear", False)
    reasoning = verdict.get("reasoning", "No reasoning provided")
    confidence = verdict.get("confidence", "")

    # Verdict dimensions
    lines.append(f"- **EFFECTIVE:** {'✓' if effective else '✗'}")
    lines.append(f"- **SAFE:** {'✓' if safe else '✗'}")
    lines.append(f"- **CLEAR:** {'✓' if clear else '✗'}")

    if confidence:
        lines.append(f"- **Confidence:** {confidence}")

    lines.append("")
    lines.append(f"**Reasoning:** {reasoning}")

    return "\n".join(lines)


def _format_interrogation(qa_pairs: List[Dict]) -> str:
    """Format interrogation Q&A pairs."""
    lines = []

    for i, qa in enumerate(qa_pairs, 1):
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        error = qa.get("error")

        lines.append(f"**Q{i}:** {question}")

        if error:
            lines.append(f"**A{i}:** *Error: {error}*")
        elif answer:
            lines.append(f"**A{i}:** {answer}")
        else:
            lines.append(f"**A{i}:** *No response*")

        lines.append("")

    return "\n".join(lines)


def _get_verdict_for_result(db: ResultsDB, result_id: int) -> Optional[Dict]:
    """Query verdict for a test result."""
    query = """
        SELECT effective, safe, clear, reasoning, passed, confidence
        FROM verdicts
        WHERE result_id = ?
    """

    result = db.conn.execute(query, (result_id,)).fetchone()

    if result:
        return {
            "effective": bool(result[0]),
            "safe": bool(result[1]),
            "clear": bool(result[2]),
            "reasoning": result[3],
            "passed": bool(result[4]),
            "confidence": result[5]
        }

    return None


def _get_interrogations_for_result(db: ResultsDB, result_id: int) -> List[Dict]:
    """Query interrogation Q&A pairs for a test result."""
    query = """
        SELECT question, answer, error
        FROM interrogations
        WHERE result_id = ?
        ORDER BY interrogation_id
    """

    results = db.conn.execute(query, (result_id,)).fetchall()

    qa_pairs = []
    for row in results:
        qa_pairs.append({
            "question": row[0],
            "answer": row[1],
            "error": row[2]
        })

    return qa_pairs
