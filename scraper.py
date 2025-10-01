# scraper.py
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

# --- Constants ---
# Using constants makes selectors easier to find and update.
TITLE_SELECTOR = 'h1.ui-pdp-title'
PRICE_SELECTOR = 'div.ui-pdp-price__second-line span.andes-money-amount__fraction'
REQUEST_TIMEOUT_SECONDS = 10

# Use logging instead of print for better control over output in production.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def _parse_price(price_text: str) -> Optional[float]:
    """
    Cleans a raw price string and converts it to a float.
    Returns None if conversion fails.
    """
    if not price_text:
        return None
    try:
        # Remove all non-digit characters (e.g., '$', '.') to handle various formats.
        cleaned_text = re.sub(r'[^\d]', '', price_text)
        return float(cleaned_text)
    except (ValueError, TypeError):
        logging.warning(f"Could not convert price text '{price_text}' to a number.")
        return None

def scrape_product(product: Dict[str, str]) -> Dict[str, Any]:
    """
    Scrapes product data, returning a structured dictionary on both success and failure.

    Args:
        product: A dictionary with 'name' and 'url' keys.

    Returns:
        A dictionary containing scraped data and a status code.
    """
    logging.info(f"Checking product: {product.get('name', 'Unknown')}")
    base_result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product_name": product.get('name'),
        "url": product.get('url'),
    }

    # Validate required input early to avoid KeyError.
    url = product.get('url')
    if not url:
        logging.error("Invalid product input: missing 'url'.")
        return {**base_result, "status": "INVALID_INPUT", "error_message": "Missing 'url'."}

    try:
        # Run the request with retry using default settings; pass headers dict (not callable)
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
        "status": "OK" if price_numeric is not None else "PARSE_ERROR"
    }
