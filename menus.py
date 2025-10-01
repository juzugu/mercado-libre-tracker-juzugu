
import json
import sqlite3
from . import config
from . import database

def load_products():
    """Tries to load the product list from products.json."""
    try:
        with open(config.PRODUCTS_FILE, 'r') as f:
            products = json.load(f)
        return products
    except FileNotFoundError:
        return []  # Return an empty list if the file doesn't exist yetf


def save_products(products):
    """Saves the product list to products.json."""
    with open(config.PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=4)  # indent=4 makes the file readable
    print(f"Product list saved to {config.PRODUCTS_FILE}")


def add_product_ui():
    """Handles the user interface for adding a new product."""
    print("\n--- Add a New Product ---")
    product_name = input("Enter the name of the product: ").strip()
    product_url = input("Enter the URL of the product: ").strip()

    if not product_name or not product_url:
        print("\n[Error] Product name and URL cannot be empty. Please try again.")
        return

    products = load_products()
    for product in products:
        if product['url'] == product_url:
            print(f"\n[Error] This URL is already being tracked as '{product['name']}'.")
            return

    new_product = {"name": product_name, "url": product_url}
    products.append(new_product)
    save_products(products)
    print(f"\nSuccess! '{product_name}' has been added to the tracking list.")

# Add this new function inside menus.py

def _select_product(prompt_message):
    """
    Displays a menu of products and prompts the user to select one.

    Args:
        prompt_message (str): The message to show the user before the list.

    Returns:
        A dictionary of the selected product, or None if the user cancels or an error occurs.
    """
    products = load_products()
    if not products:
        print("\nThere are no products to manage. Please add one first.")
        return None

    print(f"\n--- {prompt_message} ---")
    for i, product in enumerate(products, start=1):
        print(f"{i}. {product.get('name', 'N/A')}")
    print("0. Cancel")

    try:
        choice_str = input("\nEnter your choice: ")
        choice_num = int(choice_str)

        if choice_num == 0:
            return None # User chose to cancel

        product_index = choice_num - 1
        if 0 <= product_index < len(products):
            return products[product_index] # Success! Return the chosen product.
        else:
            print("\n[Error] Invalid number.")
            return None # The number was out of range

    except ValueError:
        print("\n[Error] Please enter a valid number.")
        return None # The input wasn't a number


def delete_product_ui():
    """Handles the user interface for deleting a product."""
    # This one line replaces all the menu logic!
    product_to_delete = _select_product("Select a Product to Delete")

    if not product_to_delete:
        print("Deletion cancelled.")
        return

    confirm = input(f"Are you sure you want to delete '{product_to_delete['name']}'? (y/n): ").lower()
    if confirm == 'y':
        products = load_products()
        # Filter the list to remove the product we want to delete
        products_after_deletion = [p for p in products if p['url'] != product_to_delete['url']]
        save_products(products_after_deletion)
        print(f"'{product_to_delete['name']}' has been deleted successfully.")
    else:
        print("Deletion cancelled.")

def view_product_history_ui():
    """Handles the user interface for viewing a product's price history."""
    selected_product = _select_product("Select a Product to View History")

    if not selected_product:
        return

    product_name_to_query = selected_product['name']
    
    # This function now calls your database module instead of using sqlite3 directly
    results = database.get_product_history(product_name_to_query)

    if not results:
        print(f"\nNo history found for '{product_name_to_query}'.")
    else:
        print(f"\n--- Price History for {product_name_to_query} ---")
        for row in results:
            timestamp, title, price = row
            print(f"  [{timestamp}] - {price} - {title}")