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
        return [] # Return an empty list if the file doesn't exist yetf

def save_products(products):
    """Saves the product list to products.json."""
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=4) # indent=4 makes the file readable
    print(f"Product list saved to {PRODUCTS_FILE}")
def add_product_ui():
    """Handles the user interface for adding a new product."""
    print("\n--- Add a New Product ---")
    
    # 1. Get user input
    product_name = input("Enter the name of the product: ").strip()
    product_url = input("Enter the URL of the product: ").strip()

    # 2. Safety Check: Ensure input isn't blank
    if not product_name or not product_url:
        print("\n[Error] Product name and URL cannot be empty. Please try again.")
        return # Exit the function

    # 3. Load existing products to check for duplicates
    products = load_products()
    
    # 4. Safety Check: Ensure URL isn't already tracked
    for product in products:
        if product['url'] == product_url:
            print(f"\n[Error] This URL is already being tracked as '{product['name']}'.")
            return # Exit the function

    # 5. If all checks pass, add and save
    new_product = {"name": product_name, "url": product_url}
    products.append(new_product)
    save_products(products)
    
    print(f"\nSuccess! '{product_name}' has been added to the tracking list.")
def with_retries(fn, tries=3, base_delay=1):
    """Call fn() up to `tries` times. Wait 1s, 2s, 4s ... between failures."""
    for i in range(tries):
        try:
            return fn()
        except requests.exceptions.RequestException:
            if i == tries - 1:
                raise
            time.sleep(base_delay * (2 ** i))

def run_price_checker(products_to_track):
    """
    Takes a list of products, scrapes their data, and saves it to the database.
    """
    print("\n--- Starting Price Check ---")
    with sqlite3.connect(DB_FILE) as con:
        cur = con.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                Timestamp     TEXT, ProductName   TEXT, ScrapedTitle  TEXT,
                Price         TEXT, PriceNumeric  INTEGER, Status        TEXT
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
    print(f"Price history saved to {DB_FILE}")
def main():
    """Main entry point for the application menu."""
    while True:
        print("\n--- Price Tracker Menu ---")
        print("1. Run Price Check")
        print("2. Add a New Product")
        print("3. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            products = load_products() # Load the most current list
            if products:
                run_price_checker(products)
            else:
                print("\nNo products to check. Please add a product first.")
        
        elif choice == '2':
            add_product_ui()

        elif choice == '3':
            print("Goodbye!")
            break # Exit the while loop

        else:
            print("\n[Error] Invalid choice. Please select a valid option.")

# This ensures main() is called only when the script is executed directly
if __name__ == "__main__":
    main()
    df
