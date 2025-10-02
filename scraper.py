"""Scraper: fetch title and price for a product URL, returning a structured result."""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
try:
    from . import config, utils  # package-relative
except ImportError:  # script execution fallback
    import config, utils

TITLE_SELECTOR = 'h1.ui-pdp-title'
PRICE_SELECTOR = 'div.ui-pdp-price__second-line span.andes-money-amount__fraction'
REQUEST_TIMEOUT_SECONDS = 10

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def _parse_price(price_text: str) -> Optional[float]:
    """Return numeric price from text, or None if parsing fails."""
    if not price_text:
        return None
    try:
        cleaned_text = re.sub(r'[^\d]', '', price_text)
        return float(cleaned_text)
    except (ValueError, TypeError):
        logging.warning(f"Could not convert price text '{price_text}' to a number.")
        return None


def scrape_product(product: Dict[str, str]) -> Dict[str, Any]:
    """Scrape a product dict with 'name' and 'url'; return a result payload."""
    logging.info(f"Checking product: {product.get('name', 'Unknown')}")
    base_result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product_name": product.get('name'),
        "url": product.get('url'),
    }

    url = product.get('url')
    if not url:
        logging.error("Invalid product input: missing 'url'.")
        return {**base_result, "status": "INVALID_INPUT", "error_message": "Missing 'url'."}

    try:
        response = utils.with_retries()(
            lambda: requests.get(url, headers=config.headers, timeout=REQUEST_TIMEOUT_SECONDS)
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error for {product.get('name')}: {e}")
        return {**base_result, "status": "NETWORK_ERROR", "error_message": str(e)}

    soup = BeautifulSoup(response.text, 'html.parser')
    title_element = soup.select_one(TITLE_SELECTOR)
    price_element = soup.select_one(PRICE_SELECTOR)

    if not title_element or not price_element:
        logging.warning(f"Selector miss for {product.get('name')}. Page may have changed.")
        return {**base_result, "status": "SELECTOR_MISS"}

    scraped_title = title_element.get_text(strip=True)
    price_str = price_element.get_text(strip=True)
    price_numeric = _parse_price(price_str)

    return {
        **base_result,
        "scraped_title": scraped_title,
        "price": price_str,
        "price_numeric": price_numeric,
        "status": "OK" if price_numeric is not None else "PARSE_ERROR",
    }
