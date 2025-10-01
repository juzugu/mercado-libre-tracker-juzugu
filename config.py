from typing import Final
import os

DB_FILE: Final = "price_history.db"
PRODUCTS_FILE: Final = "products.json"           # List of products to track
PRICE_HISTORY_CSV: Final = "price_history.csv"   # Price history storage

DEFAULT_USER_AGENT: Final = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

def get_request_headers(
    user_agent: str | None = None,
    accept_language: str = "es-CO,es;q=0.9,en;q=0.8",
) -> dict:
    """Build request headers with safe defaults. UA can be overridden via SCRAPER_USER_AGENT env."""
    ua = user_agent or os.getenv("SCRAPER_USER_AGENT") or DEFAULT_USER_AGENT
    return {
        "User-Agent": ua,
        "Accept-Language": accept_language,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "close",  # helps avoid flaky keep-alive issues
    }

headers = get_request_headers()
