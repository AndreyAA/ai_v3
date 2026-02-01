"""Logging utilities with context and timing support."""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Generator, Optional

from file_processor.context import get_current_context


class ContextFormatter(logging.Formatter):
    """
    Log formatter that includes processing context.

    Format: [short_uuid][STAGE] message (timing if available)
    """

    def format(self, record: logging.LogRecord) -> str:
        ctx = get_current_context()

        if ctx:
            prefix = f"[{ctx.short_id}][{ctx.stage.value:5}]"
        else:
            prefix = "[--------][-----]"

        record.context_prefix = prefix

        return super().format(record)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging with context-aware formatter.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    formatter = ContextFormatter(
        fmt="%(asctime)s %(levelname)-8s %(context_prefix)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper()))


@contextmanager
def log_timing(
    logger: logging.Logger,
    operation: str,
    level: int = logging.INFO,
) -> Generator[None, None, None]:
    """
    Context manager that logs operation duration.

    Args:
        logger: Logger instance to use.
        operation: Description of the operation being timed.
        level: Logging level for the message.

    Example:
        with log_timing(logger, "Processing chunk"):
            process_chunk(data)
    """
    start = time.perf_counter()
    logger.log(level, "%s started", operation)

    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.log(level, "%s completed in %.2f ms", operation, elapsed_ms)


def timed(
    logger: Optional[logging.Logger] = None,
    operation: Optional[str] = None,
    level: int = logging.INFO,
) -> Callable:
    """
    Decorator that logs function execution time.

    Args:
        logger: Logger instance. If None, creates one from function module.
        operation: Operation name. If None, uses function name.
        level: Logging level.

    Example:
        @timed(logger, "Data transformation")
        def transform_data(data):
            ...
    """

    def decorator(func: Callable) -> Callable:
        nonlocal logger, operation

        if logger is None:
            logger = logging.getLogger(func.__module__)
        if operation is None:
            operation = func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with log_timing(logger, operation, level):
                return func(*args, **kwargs)

        return wrapper

    return decorator
