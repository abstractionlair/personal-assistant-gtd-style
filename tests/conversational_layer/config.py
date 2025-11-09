"""Configuration management for test framework.

Provides dataclass for test configuration with defaults and validation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Test framework configuration.

    Attributes:
        # Paths
        system_prompt_path: Path to system prompt file
        test_cases_path: Path to test cases JSON
        mcp_config_path: Path to MCP config (None for simulation mode)

        # Execution
        runs: Number of times to run each test
        inter_run_delay: Delay in seconds between runs
        inter_test_delay: Delay in seconds between tests
        max_retries: Maximum retry attempts for failed operations
        initial_backoff: Initial backoff delay for retries (seconds)
        backoff_multiplier: Multiplier for exponential backoff

        # Timeouts
        assistant_timeout: Timeout for assistant execution (seconds)
        judge_timeout: Timeout for judge evaluation (seconds)
        interrogation_timeout: Timeout for interrogation questions (seconds)
        cleanup_timeout: Timeout for graph cleanup (seconds)

        # Features
        mode: Test mode ('sim' or 'real')
        clean_between_tests: Whether to clean graph between tests
        interrogate_failures: Whether to interrogate failed tests
        interrogate_passes: Whether to interrogate passed tests
        use_refactored_cases: Whether to use refactored test cases

        # Output
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARN, ERROR)
        results_db: Path to results database
        interrogation_log: Path to interrogation log (optional)
        print_assistant_on_fail: Whether to print assistant output on failure

        # CLI
        suite: Test suite to run ('assistant' or 'judge')
        category: Filter by category (optional)
        test_name: Run single test by name (optional)
        list_tests: Just list tests without running
    """

    # Paths
    system_prompt_path: Path
    test_cases_path: Path
    mcp_config_path: Optional[Path] = None

    # Execution
    runs: int = 1
    inter_run_delay: float = 10.0
    inter_test_delay: float = 0.0
    max_retries: int = 3
    initial_backoff: float = 30.0
    backoff_multiplier: float = 2.0

    # Timeouts
    assistant_timeout: float = 600.0
    judge_timeout: float = 60.0
    interrogation_timeout: float = 60.0
    cleanup_timeout: float = 120.0

    # Features
    mode: str = "sim"  # 'sim' or 'real'
    clean_between_tests: bool = False
    interrogate_failures: bool = False
    interrogate_passes: bool = False
    use_refactored_cases: bool = True

    # Output
    log_file: Path = Path("test_run.log")
    log_level: str = "INFO"
    results_db: Path = Path("test_results.db")
    interrogation_log: Optional[Path] = None
    print_assistant_on_fail: bool = False

    # CLI
    suite: str = "assistant"  # 'assistant' or 'judge'
    category: Optional[str] = None
    test_name: Optional[str] = None
    list_tests: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate mode
        if self.mode not in ("sim", "real"):
            raise ValueError(f"Invalid mode: {self.mode}. Must be 'sim' or 'real'")

        # Validate MCP config for real mode
        if self.mode == "real" and self.mcp_config_path is None:
            raise ValueError("MCP config path required for 'real' mode")

        # Validate suite
        if self.suite not in ("all", "assistant", "judge"):
            raise ValueError(f"Invalid suite: {self.suite}. Must be 'all', 'assistant', or 'judge'")

        # Validate positive numeric values
        if self.runs < 1:
            raise ValueError(f"Runs must be >= 1, got {self.runs}")

        if self.max_retries < 0:
            raise ValueError(f"Max retries must be >= 0, got {self.max_retries}")

        if self.initial_backoff < 0:
            raise ValueError(f"Initial backoff must be >= 0, got {self.initial_backoff}")

        if self.assistant_timeout <= 0:
            raise ValueError(f"Assistant timeout must be > 0, got {self.assistant_timeout}")

        # Validate paths exist
        if not self.system_prompt_path.exists():
            raise ValueError(f"System prompt not found: {self.system_prompt_path}")

        if not self.test_cases_path.exists():
            raise ValueError(f"Test cases not found: {self.test_cases_path}")

        if self.mcp_config_path and not self.mcp_config_path.exists():
            raise ValueError(f"MCP config not found: {self.mcp_config_path}")

    def is_simulation_mode(self) -> bool:
        """Check if running in simulation mode."""
        return self.mode == "sim"

    def is_live_mcp_mode(self) -> bool:
        """Check if running in live MCP mode."""
        return self.mode == "real"

    def should_clean_graph(self) -> bool:
        """Check if graph cleanup is enabled and appropriate for mode."""
        return self.clean_between_tests and self.is_live_mcp_mode()

    def should_interrogate(self, passed: bool) -> bool:
        """Check if interrogation is enabled for this result.

        Args:
            passed: Whether test passed

        Returns:
            True if should interrogate
        """
        if passed:
            return self.interrogate_passes
        else:
            return self.interrogate_failures

    def get_test_overlays(self) -> list[Path]:
        """Get test overlay paths for current mode.

        Returns:
            List of overlay file paths to append to system prompt
        """
        fixtures_dir = self.test_cases_path.parent / "fixtures"

        overlays = []

        # Always add base test overlay
        test_overlay = fixtures_dir / "system-prompt-test-overlay.md"
        if test_overlay.exists():
            overlays.append(test_overlay)

        # Add mode-specific overlay
        if self.is_live_mcp_mode():
            mcp_overlay = fixtures_dir / "system-prompt-live-mcp-overlay.md"
            if mcp_overlay.exists():
                overlays.append(mcp_overlay)
        else:
            no_mcp_overlay = fixtures_dir / "system-prompt-no-mcp-overlay.md"
            if no_mcp_overlay.exists():
                overlays.append(no_mcp_overlay)

        return overlays

    def to_dict(self) -> dict:
        """Convert config to dictionary (for serialization).

        Returns:
            Dictionary representation of config
        """
        return {
            "system_prompt_path": str(self.system_prompt_path),
            "test_cases_path": str(self.test_cases_path),
            "mcp_config_path": str(self.mcp_config_path) if self.mcp_config_path else None,
            "runs": self.runs,
            "inter_run_delay": self.inter_run_delay,
            "inter_test_delay": self.inter_test_delay,
            "max_retries": self.max_retries,
            "initial_backoff": self.initial_backoff,
            "backoff_multiplier": self.backoff_multiplier,
            "assistant_timeout": self.assistant_timeout,
            "judge_timeout": self.judge_timeout,
            "interrogation_timeout": self.interrogation_timeout,
            "cleanup_timeout": self.cleanup_timeout,
            "mode": self.mode,
            "clean_between_tests": self.clean_between_tests,
            "interrogate_failures": self.interrogate_failures,
            "interrogate_passes": self.interrogate_passes,
            "use_refactored_cases": self.use_refactored_cases,
            "log_file": str(self.log_file),
            "log_level": self.log_level,
            "results_db": str(self.results_db),
            "interrogation_log": str(self.interrogation_log) if self.interrogation_log else None,
            "print_assistant_on_fail": self.print_assistant_on_fail,
            "suite": self.suite,
            "category": self.category,
            "test_name": self.test_name,
            "list_tests": self.list_tests,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        """Create config from dictionary.

        Args:
            data: Dictionary with config values

        Returns:
            Config instance
        """
        # Convert string paths to Path objects
        for key in ('system_prompt_path', 'test_cases_path', 'mcp_config_path',
                    'log_file', 'results_db', 'interrogation_log'):
            if key in data and data[key] is not None:
                data[key] = Path(data[key])

        return cls(**data)


# Default configuration values (can be imported and modified)
DEFAULT_CONFIG = Config(
    system_prompt_path=Path("src/conversational-layer/system-prompt-full.md"),
    test_cases_path=Path("tests/test_cases_refactored.json"),
    mcp_config_path=None,  # Simulation mode by default
    mode="sim",
    runs=1,
    inter_run_delay=10.0,
    max_retries=3,
    initial_backoff=30.0,
)
