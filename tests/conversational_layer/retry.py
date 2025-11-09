"""Retry logic with exponential backoff for handling transient failures.

Provides retry decorators and functions for handling rate limits and
temporary errors in Claude API calls.
"""

import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from .logging_config import get_logger, log_retry

T = TypeVar('T')


def is_rate_limit_error(result: Dict[str, Any]) -> bool:
    """Detect if result indicates a rate limit error.

    Args:
        result: Result dictionary with optional "reason" field

    Returns:
        True if error appears to be rate-limit related

    Rate limit indicators:
        - "rate limit" in error message
        - "too many requests"
        - "429" status code
        - "quota exceeded"
        - "overloaded" server
    """
    if not isinstance(result, dict):
        return False

    reason = str(result.get("reason", "")).lower()

    rate_limit_indicators = [
        "rate limit",
        "too many requests",
        "429",
        "quota exceeded",
        "overloaded",
        "throttled",
        "capacity",
    ]

    return any(indicator in reason for indicator in rate_limit_indicators)


def is_retryable_error(result: Dict[str, Any]) -> bool:
    """Detect if result indicates a retryable error.

    Args:
        result: Result dictionary with optional "reason" and "retry" fields

    Returns:
        True if error should be retried

    Retryable errors:
        - Rate limits (detected via is_rate_limit_error)
        - Timeout errors
        - Connection errors
        - Broken pipe
        - Explicit retry flag in result
    """
    if not isinstance(result, dict):
        return False

    # Explicit retry flag
    if result.get("retry") is True:
        return True

    # Rate limit errors are always retryable
    if is_rate_limit_error(result):
        return True

    reason = str(result.get("reason", "")).lower()

    retryable_indicators = [
        "timeout",
        "connection",
        "broken pipe",
        "network",
        "temporary",
    ]

    return any(indicator in reason for indicator in retryable_indicators)


def retry_with_backoff(
    func: Callable[..., Dict[str, Any]],
    max_retries: int = 3,
    initial_backoff: float = 30.0,
    backoff_multiplier: float = 2.0,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """Execute function with exponential backoff retry.

    Args:
        func: Function to execute (must return Dict with "pass" field)
        max_retries: Maximum number of retry attempts (default: 3)
        initial_backoff: Initial backoff delay in seconds (default: 30.0)
        backoff_multiplier: Multiplier for backoff delay (default: 2.0)
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result dictionary from successful execution or final attempt

    Example:
        >>> def flaky_function():
        ...     # Might fail with rate limit
        ...     return {"pass": True, "data": "..."}
        >>>
        >>> result = retry_with_backoff(
        ...     flaky_function,
        ...     max_retries=3,
        ...     initial_backoff=30.0
        ... )
    """
    logger = get_logger()

    for attempt in range(max_retries):
        # Execute function
        result = func(*args, **kwargs)

        # Success (pass is not False, handles None/missing pass field)
        if result.get("pass") is not False:
            if attempt > 0:
                logger.info(
                    f"Retry successful on attempt {attempt + 1}",
                    extra={"attempt": attempt + 1}
                )
            return result

        # Check if error is retryable
        if not is_retryable_error(result):
            logger.debug(
                f"Non-retryable error, failing immediately: {result.get('reason', 'unknown')[:100]}",
                extra={"attempt": attempt + 1}
            )
            return result

        # Last attempt - don't retry
        if attempt >= max_retries - 1:
            logger.warning(
                f"Max retries ({max_retries}) exceeded",
                extra={"attempt": attempt + 1, "reason": result.get("reason", "")[:100]}
            )
            return result

        # Calculate backoff and wait
        backoff = initial_backoff * (backoff_multiplier ** attempt)
        log_retry(logger, attempt + 1, max_retries, backoff)
        time.sleep(backoff)

    # Should never reach here, but safety fallback
    return {"pass": False, "reason": "Max retries exceeded (fallback)"}


def retry_decorator(
    max_retries: int = 3,
    initial_backoff: float = 30.0,
    backoff_multiplier: float = 2.0
):
    """Decorator to add retry logic to functions.

    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff delay in seconds
        backoff_multiplier: Multiplier for backoff delay

    Returns:
        Decorated function with retry logic

    Example:
        >>> @retry_decorator(max_retries=3, initial_backoff=10.0)
        ... def run_assistant(prompt, config):
        ...     # Might fail with rate limit
        ...     return {"pass": True, "result": "..."}
    """

    def decorator(func: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            return retry_with_backoff(
                func,
                max_retries=max_retries,
                initial_backoff=initial_backoff,
                backoff_multiplier=backoff_multiplier,
                *args,
                **kwargs
            )

        return wrapper

    return decorator


class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff delay in seconds
        backoff_multiplier: Multiplier for exponential backoff
        enabled: Whether retry is enabled at all

    Example:
        >>> config = RetryConfig(max_retries=5, initial_backoff=60.0)
        >>> result = retry_with_backoff(func, config.max_retries, config.initial_backoff)
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff: float = 30.0,
        backoff_multiplier: float = 2.0,
        enabled: bool = True
    ):
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.enabled = enabled

    def execute_with_retry(
        self,
        func: Callable[..., Dict[str, Any]],
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute function with this retry configuration.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from function execution
        """
        if not self.enabled:
            return func(*args, **kwargs)

        return retry_with_backoff(
            func,
            max_retries=self.max_retries,
            initial_backoff=self.initial_backoff,
            backoff_multiplier=self.backoff_multiplier,
            *args,
            **kwargs
        )


def calculate_total_retry_time(
    max_retries: int,
    initial_backoff: float,
    backoff_multiplier: float = 2.0
) -> float:
    """Calculate total time spent in retries (worst case).

    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff delay
        backoff_multiplier: Multiplier for backoff

    Returns:
        Total seconds that could be spent in backoff delays

    Example:
        >>> total = calculate_total_retry_time(3, 30.0, 2.0)
        >>> print(f"Max retry time: {total}s ({total/60:.1f}min)")
        Max retry time: 210.0s (3.5min)
    """
    total = 0.0
    for attempt in range(max_retries - 1):  # -1 because last attempt doesn't wait
        total += initial_backoff * (backoff_multiplier ** attempt)
    return total
