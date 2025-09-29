# scraper.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import sqlite3
from . import config
from . import utils




def run_price_checker(products_to_track):
    """Takes a list of products, scrapes their data, and saves it to the database."""
    print("\n--- Starting Price Check ---")
    with sqlite3.connect(config.DB_FILE) as con:
        cur = con.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                Timestamp    TEXT, ProductName  TEXT, ScrapedTitle  TEXT,
                Price        TEXT, PriceNumeric INTEGER, Status      TEXT
            )
        """)
        for product in products_to_track:
            print(f"--- Checking: {product['name']} ---")
            try:
                response = utils.with_retries(lambda: requests.get(product['url'], headers=config.HEADERS, timeout=10))
                response.raise_for_status()
                html_text = response.text
                Bsoup = BeautifulSoup(html_text, 'html.parser')

                title_element = Bsoup.find('h1', class_='ui-pdp-title')
                title = title_element.text.strip() if title_element else "Title not found"

                price_selector = "div.ui-pdp-price__second-line span.andes-money-amount__fraction"
                price_element = Bsoup.select_one(price_selector)
                price = price_element.text.strip() if price_element else "Price not found"

                price_numeric = None
                if price_element:
                    try:
                        cleaned_price_string = price.replace('.', '').replace('$', '').strip()
                        price_numeric = int(cleaned_price_string)
                    except (ValueError, TypeError):
                        print(f"  - Warning: Could not convert price '{price}' to a number.")
                        price_numeric = -1

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status = "OK" if (title_element and price_element) else "SELECTOR_MISS"

                print(f"  Product: {title}")
                print(f"  Price: {price}")

                cur.execute(
                    "INSERT INTO prices (Timestamp, ProductName, ScrapedTitle, Price, PriceNumeric, Status) VALUES (?, ?, ?, ?, ?, ?)",
                    (timestamp, product['name'], title, price, price_numeric, status)
                )

                print(f"  Data successfully saved for {product['name']}")
                time.sleep(1.0)
            except requests.exceptions.RequestException as e:
                print(f"  Error fetching {product['name']}: {e}")
                continue
        con.commit()
    print("\n--- Price Check Complete ---")
    print(f"Price history saved to {config.DB_FILE}")