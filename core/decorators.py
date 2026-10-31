from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from raccoon_simple_stopwatch.stopwatch import StopWatch

from core.utils import get_logger

F = TypeVar("F", bound=Callable[..., Any])


def stop_watch(message: str) -> Callable[[F], F]:
    """Log when the decorated call starts and when it finishes, with the elapsed time.

    Args:
        message: Prefix of both log lines.

    Returns:
        A decorator that wraps the timed function.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger()
            sw = StopWatch(True)
            logger.info(f"{message}... started!")

            result = func(*args, **kwargs)

            elapsed_time = sw.end()
            logger.info(f"{message}... done! [{elapsed_time}]")
            return result

        return cast(F, wrapper)

    return decorator
