"""Results database for test framework persistence.

Provides SQLite-based storage for test results, enabling historical analysis,
flaky test detection, and result comparison across runs.
"""

import json
import sqlite3
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import Config
from .interrogation import QAPair
from .judge import Verdict
from .logging_config import get_logger
from .models import TestResult, TestSuiteResults


class ResultsDB:
    """SQLite database for test result persistence.

    Schema:
    - runs: Test run metadata
    - test_results: Individual test results
    - interrogations: Q&A pairs from interrogation
    - verdicts: Judge verdicts
    """

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = get_logger()
        self.conn: Optional[sqlite3.Connection] = None

        # Ensure database exists and tables are created
        self._init_database()

    def _init_database(self):
        """Initialize database schema if not exists."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                mode TEXT NOT NULL,
                runs_count INTEGER NOT NULL,
                test_count INTEGER NOT NULL,
                passed_count INTEGER NOT NULL,
                failed_count INTEGER NOT NULL,
                duration REAL NOT NULL,
                config_json TEXT NOT NULL
            )
        """)

        # Test results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                test_name TEXT NOT NULL,
                category TEXT NOT NULL,
                run_number INTEGER NOT NULL,
                passed INTEGER NOT NULL,
                expected_pass INTEGER NOT NULL,
                actual_pass INTEGER NOT NULL,
                reason TEXT,
                assistant_response TEXT,
                full_transcript TEXT,
                duration REAL NOT NULL,
                retry_count INTEGER NOT NULL,
                session_id TEXT,
                FOREIGN KEY (run_id) REFERENCES runs (run_id)
            )
        """)

        # Verdicts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verdicts (
                verdict_id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL,
                effective INTEGER NOT NULL,
                safe INTEGER NOT NULL,
                clear INTEGER NOT NULL,
                reasoning TEXT NOT NULL,
                passed INTEGER NOT NULL,
                confidence TEXT,
                FOREIGN KEY (result_id) REFERENCES test_results (result_id)
            )
        """)

        # Interrogations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interrogations (
                interrogation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                error TEXT,
                FOREIGN KEY (result_id) REFERENCES test_results (result_id)
            )
        """)

        # Indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_results_run_id
            ON test_results (run_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_results_test_name
            ON test_results (test_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_results_category
            ON test_results (category)
        """)

        self.conn.commit()

    def create_run(
        self,
        config: Config,
        suite_results: TestSuiteResults
    ) -> int:
        """Create a new test run record.

        Args:
            config: Test configuration
            suite_results: Suite results to save

        Returns:
            run_id for the new run
        """
        cursor = self.conn.cursor()

        # Serialize config (exclude paths for portability)
        config_dict = {
            "mode": config.mode,
            "runs": config.runs,
            "inter_run_delay": config.inter_run_delay,
            "inter_test_delay": config.inter_test_delay,
            "max_retries": config.max_retries,
            "assistant_timeout": config.assistant_timeout,
            "judge_timeout": config.judge_timeout,
            "clean_between_tests": config.clean_between_tests,
            "interrogate_failures": config.interrogate_failures,
            "interrogate_passes": config.interrogate_passes,
        }

        cursor.execute("""
            INSERT INTO runs (
                timestamp, mode, runs_count, test_count, passed_count,
                failed_count, duration, config_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            config.mode,
            config.runs,
            suite_results.total,
            suite_results.passed,
            suite_results.failed,
            suite_results.duration,
            json.dumps(config_dict)
        ))

        self.conn.commit()
        run_id = cursor.lastrowid

        self.logger.info(f"Created run record: run_id={run_id}")
        return run_id

    def save_test_result(
        self,
        run_id: int,
        result: TestResult
    ) -> int:
        """Save individual test result.

        Args:
            run_id: Run ID from create_run()
            result: Test result to save

        Returns:
            result_id for the saved result
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO test_results (
                run_id, test_name, category, run_number, passed,
                expected_pass, actual_pass, reason, assistant_response,
                full_transcript, duration, retry_count, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            result.test_name,
            result.category,
            result.run_number,
            1 if result.passed else 0,
            1 if result.expected_pass else 0,
            1 if result.actual_pass else 0,
            result.reason,
            result.assistant_response,
            result.full_transcript,
            result.duration,
            result.retry_count,
            result.session_id
        ))

        self.conn.commit()
        result_id = cursor.lastrowid

        # Save verdict if present
        if result.verdict:
            self._save_verdict(result_id, result.verdict)

        # Save interrogation if present
        if result.interrogation:
            self._save_interrogation(result_id, result.interrogation)

        return result_id

    def _save_verdict(self, result_id: int, verdict: Verdict):
        """Save judge verdict.

        Args:
            result_id: Result ID
            verdict: Verdict to save
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO verdicts (
                result_id, effective, safe, clear, reasoning, passed, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            result_id,
            1 if verdict.effective else 0,
            1 if verdict.safe else 0,
            1 if verdict.clear else 0,
            verdict.reasoning,
            1 if verdict.passed else 0,
            verdict.confidence
        ))

        self.conn.commit()

    def _save_interrogation(self, result_id: int, qa_pairs: List[QAPair]):
        """Save interrogation Q&A pairs.

        Args:
            result_id: Result ID
            qa_pairs: List of Q&A pairs
        """
        cursor = self.conn.cursor()

        for qa in qa_pairs:
            cursor.execute("""
                INSERT INTO interrogations (
                    result_id, question, answer, error
                ) VALUES (?, ?, ?, ?)
            """, (
                result_id,
                qa.question,
                qa.answer,
                qa.error
            ))

        self.conn.commit()

    def save_suite_results(
        self,
        config: Config,
        suite_results: TestSuiteResults
    ) -> int:
        """Save complete suite results (run + all test results).

        Args:
            config: Test configuration
            suite_results: Suite results to save

        Returns:
            run_id for the saved run
        """
        run_id = self.create_run(config, suite_results)

        for result in suite_results.results:
            self.save_test_result(run_id, result)

        self.logger.info(
            f"Saved suite results: run_id={run_id}, "
            f"{suite_results.total} tests, {suite_results.passed} passed"
        )

        return run_id

    def get_run_summary(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get summary for a specific run.

        Args:
            run_id: Run ID

        Returns:
            Run summary dictionary or None if not found
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM runs WHERE run_id = ?
        """, (run_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return dict(row)

    def get_test_results(self, run_id: int) -> List[Dict[str, Any]]:
        """Get all test results for a run.

        Args:
            run_id: Run ID

        Returns:
            List of test result dictionaries
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM test_results WHERE run_id = ? ORDER BY result_id
        """, (run_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_flaky_tests(
        self,
        min_runs: int = 5,
        instability_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Find flaky tests (inconsistent pass/fail across runs).

        Args:
            min_runs: Minimum number of runs to consider
            instability_threshold: Max acceptable failure rate (0.0-1.0)

        Returns:
            List of flaky test summaries with statistics
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                test_name,
                category,
                COUNT(*) as total_runs,
                SUM(passed) as pass_count,
                COUNT(*) - SUM(passed) as fail_count,
                CAST(SUM(passed) AS REAL) / COUNT(*) as pass_rate,
                AVG(duration) as avg_duration
            FROM test_results
            GROUP BY test_name, category
            HAVING total_runs >= ?
                AND pass_rate > 0
                AND pass_rate < (1.0 - ?)
            ORDER BY pass_rate ASC
        """, (min_runs, instability_threshold))

        return [dict(row) for row in cursor.fetchall()]

    def get_category_stats(self, run_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get statistics by category.

        Args:
            run_id: Optional run ID to filter by

        Returns:
            List of category statistics
        """
        cursor = self.conn.cursor()

        if run_id:
            cursor.execute("""
                SELECT
                    category,
                    COUNT(*) as total,
                    SUM(passed) as passed,
                    COUNT(*) - SUM(passed) as failed,
                    CAST(SUM(passed) AS REAL) / COUNT(*) as pass_rate,
                    AVG(duration) as avg_duration
                FROM test_results
                WHERE run_id = ?
                GROUP BY category
                ORDER BY category
            """, (run_id,))
        else:
            cursor.execute("""
                SELECT
                    category,
                    COUNT(*) as total,
                    SUM(passed) as passed,
                    COUNT(*) - SUM(passed) as failed,
                    CAST(SUM(passed) AS REAL) / COUNT(*) as pass_rate,
                    AVG(duration) as avg_duration
                FROM test_results
                GROUP BY category
                ORDER BY category
            """)

        return [dict(row) for row in cursor.fetchall()]

    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run summaries
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM runs
            ORDER BY run_id DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def export_run_to_json(self, run_id: int, output_path: Path) -> bool:
        """Export run results to JSON file.

        Args:
            run_id: Run ID to export
            output_path: Output file path

        Returns:
            True if successful
        """
        try:
            # Get run summary
            run_summary = self.get_run_summary(run_id)
            if not run_summary:
                self.logger.error(f"Run {run_id} not found")
                return False

            # Get test results
            test_results = self.get_test_results(run_id)

            # Get verdicts and interrogations
            for result in test_results:
                result_id = result["result_id"]

                # Get verdict
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT * FROM verdicts WHERE result_id = ?
                """, (result_id,))
                verdict_row = cursor.fetchone()
                if verdict_row:
                    result["verdict"] = dict(verdict_row)

                # Get interrogation
                cursor.execute("""
                    SELECT * FROM interrogations WHERE result_id = ?
                """, (result_id,))
                interrogation_rows = cursor.fetchall()
                if interrogation_rows:
                    result["interrogation"] = [dict(row) for row in interrogation_rows]

            # Build export structure
            export_data = {
                "run": run_summary,
                "test_results": test_results
            }

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)

            self.logger.info(f"Exported run {run_id} to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Export failed: {e}", exc_info=True)
            return False

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


def print_flaky_tests_report(db: ResultsDB, min_runs: int = 5):
    """Print report of flaky tests.

    Args:
        db: Results database
        min_runs: Minimum runs to consider
    """
    flaky = db.get_flaky_tests(min_runs=min_runs)

    print(f"\n{'='*70}")
    print(f"FLAKY TESTS REPORT (min {min_runs} runs)")
    print(f"{'='*70}")

    if not flaky:
        print("No flaky tests detected!")
        return

    print(f"\nFound {len(flaky)} flaky tests:\n")

    for test in flaky:
        print(f"  {test['test_name']} ({test['category']})")
        print(f"    Pass rate: {100*test['pass_rate']:.1f}% ({test['pass_count']}/{test['total_runs']})")
        print(f"    Avg duration: {test['avg_duration']:.1f}s")
        print()


def print_category_stats_report(db: ResultsDB, run_id: Optional[int] = None):
    """Print category statistics report.

    Args:
        db: Results database
        run_id: Optional run ID to filter by
    """
    stats = db.get_category_stats(run_id)

    print(f"\n{'='*70}")
    if run_id:
        print(f"CATEGORY STATISTICS (Run {run_id})")
    else:
        print(f"CATEGORY STATISTICS (All Runs)")
    print(f"{'='*70}\n")

    for cat in stats:
        print(f"{cat['category']:15} {cat['passed']:3}/{cat['total']:3} ({100*cat['pass_rate']:5.1f}%) "
              f"avg: {cat['avg_duration']:5.1f}s")
