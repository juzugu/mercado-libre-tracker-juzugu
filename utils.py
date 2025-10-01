import functools
import logging
import time
from typing import Callable, Type, Tuple

from requests.exceptions import RequestException

# Configure a basic logger for feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEFAULT_TRIES = 3
DEFAULT_DELAY_SECONDS = 1
DEFAULT_EXCEPTIONS_TO_RETRY = (RequestException,)

def retry(
    max_tries: int = DEFAULT_TRIES,
    delay_seconds: int = DEFAULT_DELAY_SECONDS,
    exceptions_to_retry: Tuple[Type[Exception], ...] = DEFAULT_EXCEPTIONS_TO_RETRY,
):
    """
    A decorator to retry a function call with exponential backoff.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions_to_retry as e:
                    last_exception = e
                    if attempt + 1 >= max_tries:
                        break  # Exit loop to raise the final exception

                    backoff_delay = delay_seconds * (2 ** attempt)
                    logging.warning(
                        "Attempt %d/%d failed for %s: %s. Retrying in %ds...",
                        attempt + 1, max_tries, func.__name__, e, backoff_delay
                    )
                    time.sleep(backoff_delay)
            
            logging.error(
                "Function %s failed after %d attempts.", func.__name__, max_tries
            )
            raise last_exception
        return wrapper
    return decorator

# Example Usage:
# @retry(max_tries=4, delay_seconds=2)
# def fetch_data(url):
#     response = requests.get(url)
#     response.raise_for_status()
#     return response.json()