# main.py

try:
    from . import menus, scraper, database
except ImportError:
    import menus, scraper, database  # script fallback
import time

_SLEEP_SECONDS = 1.0


def run_price_check():
    """Run all product scrapes, alert on price drops, and persist results."""
    products = menus.load_products()
    if not products:
        print("\nNo products to check.")
        return

    print("\n--- Starting Price Check ---")
    for product in products:
        name = product.get("name", "<unnamed>")
        try:
            scraped = scraper.scrape_product(product)
        except Exception as e:
            print(f"  [Error] {name}: unexpected error during scrape: {e}")
            time.sleep(_SLEEP_SECONDS)
            continue
        if not scraped:
            print(f"  [Skip] {name}: no data returned by scraper.")
            time.sleep(_SLEEP_SECONDS)
            continue

        price_num = scraped.get("price_numeric")
        last_price = database.get_latest_price(name)

        # Alert only on real price drops; tolerate None/missing price.
        if isinstance(price_num, (int, float)) and last_price is not None and price_num < last_price:
            print("  🎉 PRICE DROP ALERT! 🎉")
            print(f"  '{name}' dropped from ${last_price} to ${price_num}!")

        # Persist whatever the scraper produced (status explains failures).
        database.save_price_data(scraped)
        print(f"  Saved: {name} (status={scraped.get('status', 'UNKNOWN')})")

        time.sleep(_SLEEP_SECONDS)

    print("\n--- Price Check Complete ---")


def main():
    """Main entry point for the application menu."""
    database.initialize()
    while True:
        print("\n--- Price Tracker Menu ---")
        print("1. Run Price Check")
        print("2. Add a New Product")
        print("3. Delete a Product")
        print("4. View Product History")
        print("5. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            run_price_check()
        elif choice == "2":
            menus.add_product_ui()
        elif choice == "3":
            menus.delete_product_ui()
        elif choice == "4":
            menus.view_product_history_ui()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("\n[Error] Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main()
