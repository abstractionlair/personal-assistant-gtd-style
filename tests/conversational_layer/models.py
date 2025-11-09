"""Data models for test framework.

Defines dataclasses for test results and suite results to avoid circular imports.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .interrogation import QAPair
from .judge import Verdict


@dataclass
class TestResult:
    """Result from running a single test.

    Attributes:
        test_name: Name of test
        category: Test category
        run_number: Which run (1-based)
        passed: Whether test passed
        expected_pass: Whether test was expected to pass
        actual_pass: Judge verdict (pass/fail)
        reason: Explanation of result
        verdict: Full judge verdict object
        assistant_response: Extracted assistant text
        full_transcript: Full JSON output with MCP calls
        interrogation: Optional list of Q&A pairs
        duration: Test duration in seconds
        retry_count: Number of retries needed
        session_id: Session ID for resumption
    """
    test_name: str
    category: str
    run_number: int
    passed: bool
    expected_pass: bool
    actual_pass: bool
    reason: str
    verdict: Optional[Verdict] = None
    assistant_response: str = ""
    full_transcript: str = ""
    interrogation: Optional[List[QAPair]] = None
    duration: float = 0.0
    retry_count: int = 0
    session_id: str = ""


@dataclass
class TestSuiteResults:
    """Results from running entire test suite.

    Attributes:
        total: Total tests run
        passed: Number of tests that passed
        failed: Number of tests that failed
        results: List of individual test results
        interrogations: Number of interrogations performed
        duration: Total suite duration in seconds
    """
    total: int = 0
    passed: int = 0
    failed: int = 0
    results: List[TestResult] = field(default_factory=list)
    interrogations: int = 0
    duration: float = 0.0
