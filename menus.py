
# context: product persistence utilities
from pathlib import Path
from typing import List, Dict, Any
import json
import os
from urllib.parse import urlparse
from . import config, database 
def load_products() -> List[Dict[str, Any]]:
    """Load product list. Returns [] if missing/corrupt; skips invalid rows."""
    path = Path(config.PRODUCTS_FILE)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        valid: List[Dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict) and "name" in item and "url" in item:
                valid.append({"name": str(item["name"]), "url": str(item["url"])})
        return valid
    except json.JSONDecodeError:
        print(f"Warning: {path} is corrupt; starting with an empty list.")
        return []
    except OSError as e:
        print(f"Error reading {path}: {e}")
        return []



def save_products(products: List[Dict[str, Any]]) -> None:
    """Save product list atomically to avoid partial writes on crash."""
    path = Path(config.PRODUCTS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(products, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic on the same filesystem
        print(f"Product list saved to {path}")
    except OSError as e:
        print(f"Error saving to {path}: {e}")
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def _normalize_url(u: str) -> str:
    """Basic URL normalization for duplicate checks; returns '' if invalid."""
    u = u.strip()
    p = urlparse(u)
    if not p.scheme or not p.netloc:
        return ""
    path = p.path.rstrip("/") if p.path not in ("", "/") else p.path
    return f"{p.scheme.lower()}://{p.netloc.lower()}{path}{('?' + p.query) if p.query else ''}"



def add_product_ui() -> None:
    """Handles the user interface for adding a new product."""
    print("\n--- Add a New Product ---")
    try:
        product_name = input("Enter the name of the product: ").strip()
        product_url  = input("Enter the URL of the product: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[Info] Add cancelled.")
        return

    if not product_name or not product_url:
        print("\n[Error] Product name and URL cannot be empty. Please try again.")
        return

    normalized = _normalize_url(product_url)
    if not normalized:
        print("\n[Error] Invalid URL. Please include scheme and domain (e.g., https://example.com/item).")
        return

    products: List[Dict[str, Any]] = load_products()
    existing = { _normalize_url(p.get("url","")): p for p in products }
    if normalized in existing:
        print(f"\n[Error] This URL is already being tracked as '{existing[normalized]['name']}'.")
        return

    products.append({"name": product_name, "url": product_url})
    save_products(products)
    print(f"\nSuccess! '{product_name}' has been added. Now tracking {len(products)} product(s).")


def _confirm(prompt: str) -> bool:
    """Yes/No prompt accepting y/yes/s/si (case-insensitive). Defaults to No."""
    try:
        ans = input(f"{prompt} ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n[Info] Operation cancelled.")
        return False
    return ans in {"y", "yes", "s", "si"}


def delete_product_ui() -> None:
    """Handles the user interface for deleting a product."""
    product_to_delete = _select_product("Select a Product to Delete")
    if not product_to_delete:
        print("[Info] Deletion cancelled.")
        return

    if not _confirm(f"Are you sure you want to delete '{product_to_delete['name']}'? (y/n):"):
        print("Deletion cancelled.")
        return

    products = load_products()
    target_norm = _normalize_url(product_to_delete.get("url",""))
    products_after = [p for p in products if _normalize_url(p.get("url","")) != target_norm]
    save_products(products_after)
    print(f"'{product_to_delete['name']}' has been deleted successfully.")






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