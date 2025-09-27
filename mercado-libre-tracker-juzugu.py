# import the necessary libraries "tool box"
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
import json 


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



# 1. Load the products from the file
products_to_track = load_products()

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

file_exists = os.path.exists(PRICE_HISTORY_CSV)

with open(PRICE_HISTORY_CSV, 'a', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Timestamp','Product Name','Scraped Title','Price','PriceNumeric','Status'])
    if f.tell() == 0:  # to write in case is empty
        writer.writeheader()


    if not file_exists:
        writer.writeheader()

    for product in products_to_track:
        print(f"--- Checking: {product['name']} ---")
        
        try:
            response = requests.get(product['url'], headers=headers, timeout=10)
            response.raise_for_status()

            html_text = response.text
            Bsoup = BeautifulSoup(html_text, 'html.parser')
            
            title_element = Bsoup.find('h1', class_='ui-pdp-title')
            title = title_element.text.strip() if title_element else "Title not found"

            price_selector = "div.ui-pdp-price__second-line span.andes-money-amount__fraction"
            price_element = Bsoup.select_one(price_selector)
            price = price_element.text.strip() if price_element else "Price not found"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"  Product: {title}")
            print(f"  Price: {price}")
            
            writer.writerow({
                'Timestamp': timestamp,
                'Product Name': product['name'],
                'Scraped Title': title,
                'Price': price
            })
            print(f"  Data successfully saved for {product['name']}")

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching {product['name']}: {e}")
            continue