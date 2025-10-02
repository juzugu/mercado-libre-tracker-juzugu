"""Configuration and HTTP header helpers."""

from typing import Final
import os

DB_FILE: Final = "price_history.db"
PRODUCTS_FILE: Final = "products.json"            # List of products to track
PRICE_HISTORY_CSV: Final = "price_history.csv"    # Price history storage

DEFAULT_USER_AGENT: Final = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)
DEFAULT_ACCEPT_LANGUAGE: Final = "es-CO,es;q=0.9,en;q=0.8"

SCRAPER_USER_AGENT_ENV: Final = "SCRAPER_USER_AGENT"
SCRAPER_ACCEPT_LANGUAGE_ENV: Final = "SCRAPER_ACCEPT_LANGUAGE"


def get_request_headers(
    user_agent: str | None = None,
    accept_language: str = DEFAULT_ACCEPT_LANGUAGE,
) -> dict[str, str]:
    """Build HTTP request headers with safe defaults (env overrides respected)."""
    ua = user_agent or os.getenv(SCRAPER_USER_AGENT_ENV) or DEFAULT_USER_AGENT
    lang = accept_language or os.getenv(SCRAPER_ACCEPT_LANGUAGE_ENV) or DEFAULT_ACCEPT_LANGUAGE
    return {
        "User-Agent": ua,
        "Accept-Language": lang,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "close",
    }


headers = get_request_headers()
