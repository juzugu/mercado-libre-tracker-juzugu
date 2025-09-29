import time
import requests

def with_retries(fn, tries=3, base_delay=1):
    """Call fn() up to `tries` times. Wait 1s, 2s, 4s ... between failures."""
    for i in range(tries):
        try:
            return fn()
        except requests.exceptions.RequestException:
            if i == tries - 1:
                raise
            time.sleep(base_delay * (2 ** i))