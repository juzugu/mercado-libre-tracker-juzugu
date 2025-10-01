# scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from . import config, utils

def scrape_product(product):
    """
    Scrapes a single product's data from its URL.

    Args:
        product (dict): A dictionary with 'name' and 'url' keys.

    Returns:
        A dictionary with all scraped data, or None on error.
    """
    print(f"--- Checking: {product['name']} ---")
    try:
        response = utils.with_retries(lambda: requests.get(product['url'], headers=config.HEADERS, timeout=10))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title_element = soup.find('h1', class_='ui-pdp-title')
        scraped_title = title_element.text.strip() if title_element else "Title not found"

        price_selector = "div.ui-pdp-price__second-line span.andes-money-amount__fraction"
        price_element = soup.select_one(price_selector)
        price = price_element.text.strip() if price_element else "Price not found"

        price_numeric = -1
        if price_element:
            try:
                cleaned_price_string = price.replace('.', '').replace('$', '').strip()
                price_numeric = float(cleaned_price_string)
            except (ValueError, TypeError):
                print(f"  - Warning: Could not convert price '{price}' to a number.")

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "product_name": product['name'],
            "scraped_title": scraped_title,
            "price": price,
            "price_numeric": price_numeric,
            "status": "OK" if (title_element and price_element) else "SELECTOR_MISS"
        }

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching {product['name']}: {e}")
        return None