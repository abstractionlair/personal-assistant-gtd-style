#!/usr/bin/env python3
"""Conversational layer test framework - main entry point.

This is a thin wrapper around the modular test framework in
tests/conversational_layer/.

For backward compatibility, the old test_conversational_layer.py is preserved.
"""

import logging
import sys
from pathlib import Path

# Add parent to path for imports
TESTS_DIR = Path(__file__).parent
sys.path.insert(0, str(TESTS_DIR))

from conversational_layer import cli, config, runner, logging_config, results_db


def main() -> int:
    """Main entry point for test framework.

    Returns:
        Exit code (0 for success, 1 for failures)
    """
    # Parse arguments
    args = cli.parse_args()

    # Validate arguments
    cli.validate_args(args)

    # Build configuration
    try:
        test_config = cli.args_to_config(args, root=TESTS_DIR.parent)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Setup logging
    log_level = getattr(logging, test_config.log_level)
    logger = logging_config.setup_logging(test_config.log_file, log_level)

    logger.info("="*70)
    logger.info("Conversational Layer Test Framework v2.0")
    logger.info("="*70)

    # Handle query mode
    if args.query:
        try:
            db = results_db.ResultsDB(test_config.results_db)

            if args.query == "flaky":
                results_db.print_flaky_tests_report(db, min_runs=args.run_id or 5)

            elif args.query == "summary":
                if not args.run_id:
                    # Show recent runs
                    recent = db.get_recent_runs(limit=10)
                    print(f"\nRecent Test Runs:\n")
                    for run in recent:
                        print(f"  Run {run['run_id']}: {run['timestamp']}")
                        print(f"    Mode: {run['mode']}, Tests: {run['test_count']}")
                        print(f"    Passed: {run['passed_count']}/{run['test_count']} ({100*run['passed_count']/run['test_count']:.1f}%)")
                        print(f"    Duration: {run['duration']:.1f}s")
                        print()
                else:
                    # Show specific run summary
                    summary = db.get_run_summary(args.run_id)
                    if not summary:
                        print(f"ERROR: Run {args.run_id} not found", file=sys.stderr)
                        return 1
                    print(f"\nRun {summary['run_id']} Summary:\n")
                    print(f"  Timestamp: {summary['timestamp']}")
                    print(f"  Mode: {summary['mode']}")
                    print(f"  Tests: {summary['test_count']}")
                    print(f"  Passed: {summary['passed_count']} ({100*summary['passed_count']/summary['test_count']:.1f}%)")
                    print(f"  Failed: {summary['failed_count']}")
                    print(f"  Duration: {summary['duration']:.1f}s")

            elif args.query == "category":
                results_db.print_category_stats_report(db, run_id=args.run_id)

            elif args.query == "export":
                if not args.export_json:
                    print("ERROR: --export-json required for export query", file=sys.stderr)
                    return 1
                if not args.run_id:
                    print("ERROR: --run-id required for export query", file=sys.stderr)
                    return 1

                export_path = Path(args.export_json)
                if db.export_run_to_json(args.run_id, export_path):
                    print(f"Exported run {args.run_id} to {export_path}")
                else:
                    print(f"ERROR: Export failed", file=sys.stderr)
                    return 1

            db.close()
            return 0

        except Exception as e:
            print(f"ERROR: Query failed: {e}", file=sys.stderr)
            logger.error(f"Query error: {e}", exc_info=True)
            return 1

    # List tests if requested
    if test_config.list_tests:
        cases = runner.load_test_cases(test_config)
        filtered = runner.filter_test_cases(cases, test_config)
        print(f"\nFound {len(filtered)} tests:")
        for case in filtered:
            print(f"  - {case['name']} ({case['category']})")
        return 0

    # Run test suite
    try:
        results = runner.run_test_suite(test_config)
    except KeyboardInterrupt:
        logger.warning("\nTest suite interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error running test suite: {e}", exc_info=True)
        return 1

    # Print summary
    runner.print_suite_summary(results, test_config)

    # Exit with status
    if results.failed > 0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
