"""Error handling utilities for test framework.

Provides safe error handling for subprocess calls, broken pipes,
and other common failure modes in test execution.
"""

import subprocess
import sys
from typing import Any, Dict, Optional

from .logging_config import get_logger, log_error


def safe_print(text: str, flush: bool = True) -> None:
    """Print with broken pipe protection.

    Args:
        text: Text to print
        flush: Whether to flush stdout after printing

    Handles broken pipe errors gracefully by redirecting stdout to /dev/null.
    This prevents the entire test suite from crashing if output is piped to
    a process that terminates early.
    """
    try:
        print(text)
        if flush:
            sys.stdout.flush()
    except BrokenPipeError:
        # Redirect stdout to devnull to prevent further broken pipe errors
        devnull = open('/dev/null', 'w')
        sys.stdout = devnull
    except Exception:
        # Silently ignore other print errors
        pass


def flush_output() -> None:
    """Flush all output buffers to ensure data is written.

    Call this after each test to ensure progress is visible even if
    the test suite crashes. Prevents data loss in logs and results.
    """
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except (BrokenPipeError, OSError):
        # Ignore errors during flush
        pass


def handle_subprocess_error(
    error: Exception,
    context: str,
    command: Optional[list] = None
) -> Dict[str, Any]:
    """Convert subprocess exception to result dictionary.

    Args:
        error: Exception that occurred
        context: Description of where error occurred (e.g., "assistant execution")
        command: Command that was run (optional, for logging)

    Returns:
        Result dictionary with pass=False, reason, and retry flag

    Handles:
        - TimeoutExpired: Subprocess exceeded timeout (retryable)
        - CalledProcessError: Subprocess returned non-zero exit code
        - BrokenPipeError: Output pipe was closed (retryable)
        - Other exceptions: Unexpected errors

    Example:
        >>> try:
        ...     result = subprocess.run(["claude", ...], timeout=60, check=True)
        ... except Exception as e:
        ...     return handle_subprocess_error(e, "run_assistant", ["claude", ...])
    """
    logger = get_logger()

    if isinstance(error, subprocess.TimeoutExpired):
        timeout_s = error.timeout
        logger.error(
            f"Timeout in {context}: {timeout_s}s exceeded",
            extra={"context": context, "timeout": timeout_s}
        )

        return {
            "pass": False,
            "reason": f"Timeout ({timeout_s}s exceeded)",
            "retry": True,  # Timeouts are retryable
            "error_type": "timeout"
        }

    elif isinstance(error, BrokenPipeError):
        logger.error(
            f"Broken pipe in {context}",
            extra={"context": context}
        )
        safe_print(f"ERROR: Broken pipe in {context}")

        return {
            "pass": False,
            "reason": "Broken pipe",
            "retry": True,  # Broken pipes are retryable
            "error_type": "broken_pipe"
        }

    elif isinstance(error, subprocess.CalledProcessError):
        stderr = error.stderr if hasattr(error, 'stderr') else ""
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', errors='replace')

        logger.error(
            f"Process error in {context}: {stderr[:200]}",
            extra={"context": context, "returncode": error.returncode}
        )

        # Check if stderr indicates a retryable error
        retry = is_retryable_subprocess_error(stderr)

        return {
            "pass": False,
            "reason": f"Process failed (exit {error.returncode}): {stderr[:200]}",
            "retry": retry,
            "error_type": "process_error",
            "returncode": error.returncode
        }

    elif isinstance(error, FileNotFoundError):
        logger.error(
            f"File not found in {context}: {error.filename}",
            extra={"context": context, "filename": error.filename}
        )

        return {
            "pass": False,
            "reason": f"File not found: {error.filename}",
            "retry": False,  # File not found is not retryable
            "error_type": "file_not_found"
        }

    elif isinstance(error, PermissionError):
        logger.error(
            f"Permission denied in {context}: {error}",
            extra={"context": context}
        )

        return {
            "pass": False,
            "reason": f"Permission denied: {str(error)[:200]}",
            "retry": False,  # Permission errors not retryable
            "error_type": "permission_denied"
        }

    else:
        # Unexpected error - log with full stack trace
        log_error(logger, error, context)

        return {
            "pass": False,
            "reason": f"Unexpected error: {type(error).__name__}: {str(error)[:200]}",
            "retry": False,  # Unknown errors not retryable by default
            "error_type": "unexpected"
        }


def is_retryable_subprocess_error(stderr: str) -> bool:
    """Determine if subprocess error is retryable based on stderr.

    Args:
        stderr: Standard error output from subprocess

    Returns:
        True if error appears retryable

    Retryable indicators:
        - Rate limit messages
        - Connection errors
        - Timeout messages
        - Server overload
    """
    if not stderr:
        return False

    stderr_lower = stderr.lower()

    retryable_indicators = [
        "rate limit",
        "too many requests",
        "429",
        "quota exceeded",
        "overloaded",
        "connection",
        "timeout",
        "temporary",
        "throttled",
    ]

    return any(indicator in stderr_lower for indicator in retryable_indicators)


class TestFrameworkError(Exception):
    """Base exception for test framework errors.

    Use for errors specific to test framework logic (not subprocess failures).
    """
    pass


class MCPServerError(TestFrameworkError):
    """MCP server connection or communication error."""
    pass


class FixtureSetupError(TestFrameworkError):
    """Graph fixture setup failed."""
    pass


class JudgeError(TestFrameworkError):
    """Judge evaluation failed."""
    pass


class InterrogationError(TestFrameworkError):
    """Interrogation session failed."""
    pass


def format_error_for_display(error: Dict[str, Any], verbose: bool = False) -> str:
    """Format error dictionary for user-friendly display.

    Args:
        error: Error dictionary from handle_subprocess_error
        verbose: Whether to include full details

    Returns:
        Formatted error string

    Example:
        >>> error = {"pass": False, "reason": "Timeout (60s)", "error_type": "timeout"}
        >>> print(format_error_for_display(error))
        ERROR [timeout]: Timeout (60s)
    """
    reason = error.get("reason", "Unknown error")
    error_type = error.get("error_type", "unknown")

    if verbose:
        parts = [f"ERROR [{error_type}]:", reason]

        if "returncode" in error:
            parts.append(f"(exit code: {error['returncode']})")

        if error.get("retry"):
            parts.append("[retryable]")

        return " ".join(parts)
    else:
        return f"ERROR [{error_type}]: {reason[:100]}"


def wrap_subprocess_call(
    func_name: str,
    command: list,
    timeout: Optional[float] = None,
    check: bool = False,
    **subprocess_kwargs
) -> Dict[str, Any]:
    """Wrapper for subprocess calls with comprehensive error handling.

    Args:
        func_name: Name of calling function (for error context)
        command: Command list for subprocess
        timeout: Optional timeout in seconds
        check: Whether to check return code
        **subprocess_kwargs: Additional arguments for subprocess.run

    Returns:
        Result dictionary with pass/fail, output, and error info

    Example:
        >>> result = wrap_subprocess_call(
        ...     "run_assistant",
        ...     ["claude", "--print", "test prompt"],
        ...     timeout=60.0,
        ...     capture_output=True,
        ...     text=True
        ... )
        >>> if result["pass"]:
        ...     print(result["stdout"])
    """
    logger = get_logger()

    try:
        result = subprocess.run(
            command,
            timeout=timeout,
            check=check,
            **subprocess_kwargs
        )

        return {
            "pass": result.returncode == 0,
            "stdout": getattr(result, 'stdout', ''),
            "stderr": getattr(result, 'stderr', ''),
            "returncode": result.returncode
        }

    except Exception as e:
        return handle_subprocess_error(e, func_name, command)
