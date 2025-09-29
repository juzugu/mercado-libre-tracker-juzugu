# main.py

from . import menus
from . import scraper
from . import database 
import time

def run_price_check():
    """The 'conductor' function that now also checks for price drops."""
    products = menus.load_products()
    if not products:
        print("\nNo products to check.")
        return

    print("\n--- Starting Price Check ---")
    for product in products:
        scraped_data = scraper.scrape_product(product)

        if scraped_data and scraped_data['price_numeric'] > 0:
            # Get the last known price from the database
            last_price = database.get_latest_price(product['name'])

            # Compare the prices and print an alert
            if last_price is not None and scraped_data['price_numeric'] < last_price:
                print(f"  🎉 PRICE DROP ALERT! 🎉")
                print(f"  '{product['name']}' dropped from ${last_price} to ${scraped_data['price_numeric']}!")
            
            # We always save the new price
            database.save_price_data(scraped_data)
            print(f"  Data successfully saved for {product['name']}")
        
        time.sleep(1.0)
    
    print("\n--- Price Check Complete ---")


def main():
    """Main entry point for the application menu."""
    while True:
        print("\n--- Price Tracker Menu ---")
        print("1. Run Price Check")
        print("2. Add a New Product")
        print("3. Delete a Product")
        print("4. View Product History")
        print("5. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            run_price_check()
        elif choice == '2':
            menus.add_product_ui()
        elif choice == '3':
            menus.delete_product_ui()
        elif choice == '4':
            menus.view_product_history_ui()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("\n[Error] Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main()