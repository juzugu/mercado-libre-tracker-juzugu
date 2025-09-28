# import the necessary libraries "tool box"
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
import json 
import time
import sqlite3

DB_FILE = 'price_history.db'

PRODUCTS_FILE = 'products.json' # File to store the list of products to track
PRICE_HISTORY_CSV = 'price_history.csv' # File to store the price history

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def load_products():
    """Tries to load the product list from products.json."""
    try:
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)
        return products
    except FileNotFoundError:
        return [] # Return an empty list if the file doesn't exist yet

def save_products(products):
    """Saves the product list to products.json."""
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=4) # indent=4 makes the file readable
    print(f"Product list saved to {PRODUCTS_FILE}")

def with_retries(fn, tries=3, base_delay=1):
    """Call fn() up to `tries` times. Wait 1s, 2s, 4s ... between failures."""
    for i in range(tries):
        try:
            return fn()
        except requests.exceptions.RequestException:
            if i == tries - 1:
                raise
            time.sleep(base_delay * (2 ** i))


# 1. Load the products from the file
products_to_track = load_products()

# Remove duplicate URLs, to avoid run to rusl which are the same productº
seen = set()
products_to_track = [
    p for p in products_to_track
    if p.get('url') and not (p['url'] in seen or seen.add(p['url']))
]


# 2. If the list is empty, ask the user for the first product
if not products_to_track:
    print("No products found. Let's add the first one.")
    
    # Here is the input() code we talked about
    product_name = input("Enter the name of the product: ")
    product_url = input("Enter the URL of the product: ")
    
    # Create the dictionary and add it to our list
    products_to_track.append({
        "name": product_name,
        "url": product_url
    })
    
    # Save the new list to the file for the next run
    save_products(products_to_track)

# 3. Proceed with scraping (this part is mostly the same as before)
print("\n--- Starting Price Check ---")


with sqlite3.connect(DB_FILE) as con:
    cur = con.cursor()

    # Optional but recommended pragmas: speed + durability
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")

    # Make sure table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            Timestamp     TEXT,
            ProductName   TEXT,
            ScrapedTitle  TEXT,
            Price         TEXT,
            PriceNumeric  INTEGER,
            Status        TEXT
        )
    """)



    for product in products_to_track:
        print(f"--- Checking: {product['name']} ---")

        try:
            response = with_retries(lambda: requests.get(product['url'], headers=headers, timeout=10))
            response.raise_for_status()

            html_text = response.text
            Bsoup = BeautifulSoup(html_text, 'html.parser')
            
            title_element = Bsoup.find('h1', class_='ui-pdp-title')
            title = title_element.text.strip() if title_element else "Title not found"

            price_selector = "div.ui-pdp-price__second-line span.andes-money-amount__fraction"
            price_element = Bsoup.select_one(price_selector)
            price = price_element.text.strip() if price_element else "Price not found"

            price_numeric = None # Start with None for clarity
            if price_element:
                try:
                    # Clean the string by removing dots, dollar signs, and whitespace in case mercado libre change that 
                    cleaned_price_string = price.replace('.', '').replace('$', '').strip()
                    price_numeric = int(cleaned_price_string)
                except (ValueError, TypeError):
                    # If conversion fails, log a warning and set a sentinel value
                    print(f"  - Warning: Could not convert price '{price}' to a number.")
                    price_numeric = -1          
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "OK" if (title_element and price_element) else "SELECTOR_MISS"

            print(f"  Product: {title}")
            print(f"  Price: {price}")
            
            cur.execute(
            "INSERT INTO prices (Timestamp, ProductName, ScrapedTitle, Price, PriceNumeric, Status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, product['name'], title, price, price_numeric, status)
                    )



            print(f"  Data successfully saved for {product['name']}")
            time.sleep(1.0) #this is to avoid being blocked by the server because to many interactions in a short time
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching {product['name']}: {e}")
            continue
    con.commit()
print("\n--- Price Check Complete ---")
print(f"Price history saved to {DB_FILE}")
