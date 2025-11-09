"""Structured logging configuration for test framework.

Provides rotating file handlers with timestamps, log levels, and context.
Logs go to both file and console with different formatting.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Path = Path("test_run.log"),
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Setup structured logging with file and console handlers.

    Args:
        log_file: Path to log file (will be rotated when full)
        level: Logging level (DEBUG, INFO, WARN, ERROR)
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(Path("tests.log"), logging.DEBUG)
        >>> logger.info("Starting test suite", extra={"test_count": 30})
        >>> logger.error("Test failed", extra={"test_name": "capture_simple"})
    """
    logger = logging.getLogger("conv_layer_tests")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with detailed formatting
    file_handler = RotatingFileHandler(
        str(log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)-8s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler with simpler formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger() -> logging.Logger:
    """Get existing logger instance.

    Returns:
        Logger instance (must be setup first via setup_logging)
    """
    return logging.getLogger("conv_layer_tests")


class TestContextFilter(logging.Filter):
    """Add test context to log records.

    Example:
        >>> logger.addFilter(TestContextFilter())
        >>> logger.info("Running test", extra={"test_name": "capture_simple", "run": 1})
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add test context fields to record if available."""
        # Add test_name if not present
        if not hasattr(record, 'test_name'):
            record.test_name = "unknown"

        # Add run number if not present
        if not hasattr(record, 'run'):
            record.run = 0

        return True


def log_test_start(logger: logging.Logger, test_name: str, run: int, total_runs: int):
    """Log test start with context.

    Args:
        logger: Logger instance
        test_name: Name of test being run
        run: Current run number (1-based)
        total_runs: Total number of runs
    """
    logger.info(
        f"Starting test: {test_name} (run {run}/{total_runs})",
        extra={"test_name": test_name, "run": run}
    )


def log_test_result(
    logger: logging.Logger,
    test_name: str,
    passed: bool,
    reason: Optional[str] = None,
    duration: Optional[float] = None
):
    """Log test result with context.

    Args:
        logger: Logger instance
        test_name: Name of test
        passed: Whether test passed
        reason: Reason for failure (if applicable)
        duration: Test duration in seconds (if available)
    """
    status = "PASS" if passed else "FAIL"
    msg = f"Test {status}: {test_name}"

    if duration:
        msg += f" ({duration:.2f}s)"

    if not passed and reason:
        msg += f" - {reason[:100]}"

    log_func = logger.info if passed else logger.error
    log_func(msg, extra={"test_name": test_name, "passed": passed})


def log_retry(logger: logging.Logger, attempt: int, max_attempts: int, backoff: float):
    """Log retry attempt.

    Args:
        logger: Logger instance
        attempt: Current attempt number (1-based)
        max_attempts: Maximum attempts
        backoff: Backoff delay in seconds
    """
    logger.warning(
        f"Retry attempt {attempt}/{max_attempts}, waiting {backoff:.1f}s...",
        extra={"attempt": attempt, "backoff": backoff}
    )


def log_error(logger: logging.Logger, error: Exception, context: str):
    """Log error with context and stack trace.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Context string describing where error occurred
    """
    logger.error(
        f"Error in {context}: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra={"context": context, "error_type": type(error).__name__}
    )
