# import the necessary libraries "tool box"
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os

CSV_FILE = 'price_history.csv'
products_to_track = [
    {
        "name": "Pepper Gel Sabre",
        "url": "https://www.mercadolibre.com.co/pepper-gel-sabre-aim-and-fire-w-trigger-45m-range/p/MCO2027801104"
    },
    {
        "name": "Another Product",
        "url": "https://www.example.com/not-a-real-product" # Example of a URL that might fail
    }
]
#i added headers to mimic a real browser request(this is important to avoid being blocked by some websites)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

file_exists = os.path.exists(CSV_FILE)

with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Timestamp', 'Product Name', 'Scraped Title', 'Price']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    if not file_exists:
        writer.writeheader()

    for product in products_to_track:
        print(f"--- Checking price for: {product['name']} ---")
        
        try:
            #(i get this from the REQUESTS documentation)
            response = requests.get(product['url'], headers=headers, timeout=10)
            response.raise_for_status() # This will raise an error for 4xx or 5xx responses

            html_text = response.text
            Bsoup = BeautifulSoup(html_text, 'html.parser')
            
            title_element = Bsoup.find('h1', class_='ui-pdp-title')
            if title_element:  # check if it find anything
                title = title_element.text.strip()
            else:
                title = "Title not found"

            price_selector = "div.ui-pdp-price__second-line span.andes-money-amount__fraction"
            price_element = Bsoup.select_one(price_selector)    #this is for check if the price element was found
            if price_element:
                price = price_element.text.strip()
            else:
                price = "Price not found"
            
            # Formats the current time as: YYYY-MM-DD HH:MM:SS
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"Timestamp: {timestamp}")
            print(f"Product: {title}")
            print(f"Price: {price}")
            
            writer.writerow({
                'Timestamp': timestamp,
                'Product Name': product['name'],
                'Scraped Title': title,
                'Price': price
            })
            print(f"Data successfully saved for {product['name']}")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {product['name']}: {e}")
            continue