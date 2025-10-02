
import functools
import logging
import time
from typing import Callable, Tuple, Type, TypeVar

from requests.exceptions import RequestException

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_TRIES = 3
DEFAULT_DELAY_SECONDS = 1
DEFAULT_EXCEPTIONS_TO_RETRY: Tuple[Type[Exception], ...] = (RequestException,)

T = TypeVar("T")


def with_retries(
    max_tries: int = DEFAULT_TRIES,
    delay_seconds: int = DEFAULT_DELAY_SECONDS,
    exceptions_to_retry: Tuple[Type[Exception], ...] = DEFAULT_EXCEPTIONS_TO_RETRY,
) -> Callable[[Callable[[], T]], T]:
    """Run a zero-arg callable with retries and backoff."""
    def runner(thunk: Callable[[], T]) -> T:
        last_exc: Exception | None = None
        for attempt in range(max_tries):
            try:
                return thunk()
            except exceptions_to_retry as e:  # type: ignore[misc]
                last_exc = e
                if attempt + 1 >= max_tries:
                    break
                sleep_for = delay_seconds * (2 ** attempt)
                logging.warning("Retry %d/%d after error: %s (sleep %.1fs)", attempt + 1, max_tries, e, sleep_for)
                time.sleep(sleep_for)
        assert last_exc is not None
        raise last_exc
    return runner


def retry(
    max_tries: int = DEFAULT_TRIES,
    delay_seconds: int = DEFAULT_DELAY_SECONDS,
    exceptions_to_retry: Tuple[Type[Exception], ...] = DEFAULT_EXCEPTIONS_TO_RETRY,
):
    """Decorator: retry the wrapped function with backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            runner = with_retries(max_tries, delay_seconds, exceptions_to_retry)
            return runner(lambda: func(*args, **kwargs))
        return wrapper
    return decorator
