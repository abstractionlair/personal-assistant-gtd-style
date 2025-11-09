"""Command-line interface for test framework.

Provides argument parsing and configuration building from CLI arguments.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .config import Config


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Optional argument list (defaults to sys.argv)

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Run conversational layer eval tests via Claude CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests once in simulation mode
  %(prog)s --mode sim

  # Run 5 times with delays between runs
  %(prog)s --mode sim --runs 5 --inter-run-delay 10

  # Run specific category with Live MCP
  %(prog)s --mode real --category Capture --clean-graph-between-tests

  # Interrogate failures and save to JSON
  %(prog)s --mode sim --interrogate-failures --interrogation-log results.json

  # Run single test
  %(prog)s --mode sim --test-name capture_simple_task
"""
    )

    # Test selection
    parser.add_argument(
        "--case",
        dest="cases",
        action="append",
        help="Run only the named test case (repeatable)."
    )
    parser.add_argument(
        "--category",
        dest="category",
        type=str,
        default=None,
        help="Filter tests by category (Capture, Query, Update, Delete, Edge)."
    )
    parser.add_argument(
        "--test-name",
        dest="test_name",
        type=str,
        default=None,
        help="Run only the test with this specific name."
    )
    parser.add_argument(
        "--list",
        dest="list_tests",
        action="store_true",
        help="List all tests and exit (don't run)."
    )

    # Suite selection
    parser.add_argument(
        "--suite",
        dest="suite",
        choices=["all", "assistant", "judge"],
        default="all",
        help="Which suite to run: assistant (system-prompt), judge (judge rubric), or all."
    )

    # Mode
    parser.add_argument(
        "--mode",
        dest="mode",
        choices=["auto", "sim", "real"],
        default="auto",
        help="Simulate without MCP (sim), require MCP (real), or auto-detect (auto)."
    )

    # Test files
    parser.add_argument(
        "--test-cases",
        dest="test_cases_file",
        default=None,
        help="Path to test cases JSON file (default: test_cases_refactored.json)."
    )

    # Phase 1 improvement: N-run execution with delays
    parser.add_argument(
        "--runs",
        dest="runs",
        type=int,
        default=1,
        help="Number of times to run each test (default: 1)."
    )
    parser.add_argument(
        "--inter-run-delay",
        dest="inter_run_delay",
        type=float,
        default=10.0,
        help="Delay in seconds between runs (default: 10.0)."
    )
    parser.add_argument(
        "--inter-test-delay",
        dest="inter_test_delay",
        type=float,
        default=0.0,
        help="Delay in seconds between tests within a run (default: 0.0)."
    )

    # Phase 1 improvement: Retry configuration
    parser.add_argument(
        "--max-retries",
        dest="max_retries",
        type=int,
        default=3,
        help="Maximum retry attempts for failed operations (default: 3)."
    )
    parser.add_argument(
        "--initial-backoff",
        dest="initial_backoff",
        type=float,
        default=30.0,
        help="Initial backoff delay for retries in seconds (default: 30.0)."
    )

    # Timeouts
    parser.add_argument(
        "--assistant-timeout",
        dest="assistant_timeout",
        type=int,
        default=int(os.environ.get("CLAUDE_TIMEOUT_ASSISTANT", os.environ.get("CLAUDE_TIMEOUT", 600))),
        help="Timeout in seconds for assistant calls (default: 600)."
    )
    parser.add_argument(
        "--judge-timeout",
        dest="judge_timeout",
        type=int,
        default=int(os.environ.get("CLAUDE_TIMEOUT_JUDGE", os.environ.get("CLAUDE_TIMEOUT", 60))),
        help="Timeout in seconds for judge calls (default: 60)."
    )
    parser.add_argument(
        "--interrogation-timeout",
        dest="interrogation_timeout",
        type=int,
        default=60,
        help="Timeout in seconds for each interrogation question (default: 60)."
    )
    parser.add_argument(
        "--cleanup-timeout",
        dest="cleanup_timeout",
        type=int,
        default=120,
        help="Timeout in seconds for graph cleanup (default: 120)."
    )

    # Interrogation
    parser.add_argument(
        "--interrogate-failures",
        dest="interrogate_failures",
        action="store_true",
        help="Ask follow-up questions when tests fail to understand why."
    )
    parser.add_argument(
        "--interrogate-passes",
        dest="interrogate_passes",
        action="store_true",
        help="Survey the assistant when tests pass to evaluate instruction quality."
    )
    parser.add_argument(
        "--interrogate-all",
        dest="interrogate_all",
        action="store_true",
        help="Interrogate both passes and failures."
    )
    parser.add_argument(
        "--interrogation-log",
        dest="interrogation_log",
        default=None,
        help="Save detailed interrogation transcripts to JSON file."
    )

    # Graph cleanup
    parser.add_argument(
        "--clean-graph-between-tests",
        dest="clean_graph_between_tests",
        action="store_true",
        help="Delete all graph nodes between tests in Live MCP mode (ensures test isolation)."
    )

    # Output
    parser.add_argument(
        "--log-file",
        dest="log_file",
        type=str,
        default="test_run.log",
        help="Path to log file (default: test_run.log)."
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)."
    )
    parser.add_argument(
        "--print-assistant-on-fail",
        dest="print_assistant_on_fail",
        action="store_true",
        help="Print full assistant response when tests fail."
    )

    # Phase 5: Results database
    parser.add_argument(
        "--results-db",
        dest="results_db",
        type=str,
        default="test_results.db",
        help="Path to results database (default: test_results.db)."
    )
    parser.add_argument(
        "--query",
        dest="query",
        choices=["flaky", "summary", "category", "export"],
        default=None,
        help="Query test results database instead of running tests."
    )
    parser.add_argument(
        "--run-id",
        dest="run_id",
        type=int,
        default=None,
        help="Run ID for database queries."
    )
    parser.add_argument(
        "--export-json",
        dest="export_json",
        type=str,
        default=None,
        help="Export path for --query export."
    )

    return parser.parse_args(args)


def args_to_config(args: argparse.Namespace, root: Optional[Path] = None) -> Config:
    """Convert parsed arguments to Config object.

    Args:
        args: Parsed arguments from parse_args()
        root: Optional root directory (defaults to project root)

    Returns:
        Config instance

    Raises:
        ValueError: If configuration is invalid
    """
    if root is None:
        root = Path(__file__).parent.parent.parent

    # Determine mode
    mode = args.mode
    if mode == "auto":
        # Auto-detect based on MCP config availability
        mcp_default = root / "tests" / "mcp-config.json"
        mcp_override = os.environ.get("MCP_CONFIG_PATH")
        mcp_candidate = Path(mcp_override).expanduser() if mcp_override else mcp_default
        mode = "real" if mcp_candidate.exists() else "sim"

    # MCP config path
    if mode == "real":
        mcp_override = os.environ.get("MCP_CONFIG_PATH")
        if mcp_override:
            mcp_config_path = Path(mcp_override).expanduser()
        else:
            mcp_config_path = root / "tests" / "mcp-config.json"

        if not mcp_config_path.exists():
            print(f"ERROR: MCP config not found at {mcp_config_path}", file=sys.stderr)
            print("       Set MCP_CONFIG_PATH or run with --mode sim", file=sys.stderr)
            sys.exit(1)
    else:
        mcp_config_path = None

    # System prompt path
    system_prompt_path = root / "src" / "conversational-layer" / "system-prompt-full.md"
    if not system_prompt_path.exists():
        print(f"ERROR: System prompt not found at {system_prompt_path}", file=sys.stderr)
        sys.exit(1)

    # Test cases path
    if args.test_cases_file:
        test_cases_path = Path(args.test_cases_file)
    else:
        test_cases_path = root / "tests" / "test_cases_refactored.json"

    use_refactored = "refactored" in str(test_cases_path)

    if not test_cases_path.exists():
        print(f"ERROR: Test cases not found at {test_cases_path}", file=sys.stderr)
        sys.exit(1)

    # Handle interrogate-all flag
    interrogate_failures = args.interrogate_failures or args.interrogate_all
    interrogate_passes = args.interrogate_passes or args.interrogate_all

    # Build config
    config = Config(
        # Paths
        system_prompt_path=system_prompt_path,
        test_cases_path=test_cases_path,
        mcp_config_path=mcp_config_path,
        # Execution
        runs=args.runs,
        inter_run_delay=args.inter_run_delay,
        inter_test_delay=args.inter_test_delay,
        max_retries=args.max_retries,
        initial_backoff=args.initial_backoff,
        # Timeouts
        assistant_timeout=float(args.assistant_timeout),
        judge_timeout=float(args.judge_timeout),
        interrogation_timeout=float(args.interrogation_timeout),
        cleanup_timeout=float(args.cleanup_timeout),
        # Features
        mode=mode,
        clean_between_tests=args.clean_graph_between_tests,
        interrogate_failures=interrogate_failures,
        interrogate_passes=interrogate_passes,
        use_refactored_cases=use_refactored,
        # Output
        log_file=Path(args.log_file),
        log_level=args.log_level,
        results_db=Path(args.results_db),
        interrogation_log=Path(args.interrogation_log) if args.interrogation_log else None,
        print_assistant_on_fail=args.print_assistant_on_fail or bool(os.environ.get("PRINT_ASSISTANT_ON_FAIL")),
        # CLI
        suite=args.suite,
        category=args.category,
        test_name=args.test_name,
        list_tests=args.list_tests,
    )

    return config


def validate_args(args: argparse.Namespace) -> None:
    """Validate argument combinations.

    Args:
        args: Parsed arguments

    Raises:
        SystemExit: If arguments are invalid
    """
    # Check query mode requirements
    if args.query and args.query != "flaky":
        if not args.run_id:
            print("ERROR: --query requires --run-id (except for 'flaky' query)", file=sys.stderr)
            sys.exit(1)

    if args.query == "export" and not args.export_json:
        print("ERROR: --query export requires --export-json", file=sys.stderr)
        sys.exit(1)

    # Check runs value
    if args.runs < 1:
        print(f"ERROR: --runs must be >= 1, got {args.runs}", file=sys.stderr)
        sys.exit(1)

    # Check delays
    if args.inter_run_delay < 0:
        print(f"ERROR: --inter-run-delay must be >= 0, got {args.inter_run_delay}", file=sys.stderr)
        sys.exit(1)

    if args.inter_test_delay < 0:
        print(f"ERROR: --inter-test-delay must be >= 0, got {args.inter_test_delay}", file=sys.stderr)
        sys.exit(1)
