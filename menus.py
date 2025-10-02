# context: product persistence utilities
from pathlib import Path
from typing import List, Dict, Any
import json
import os
from urllib.parse import urlparse
try:
    from . import config, database  # package-relative
except ImportError:  # script execution fallback
    import config, database


def load_products() -> List[Dict[str, Any]]:
    """Load the product list from PRODUCTS_FILE.

    Returns:
        A list of {"name": str, "url": str} dicts.
        Returns [] if the file is missing, corrupt, or unreadable.
        Skips any items that don’t have both 'name' and 'url'.
    """
    path = Path(config.PRODUCTS_FILE)

    # If the file doesn’t exist yet, start with an empty list.
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Expect a list of dicts; anything else => empty list.
        if not isinstance(data, list):
            return []

        # Keep only well-formed items; coerce fields to str for safety.
        valid: List[Dict[str, Any]] = [
            {"name": str(item["name"]), "url": str(item["url"])}
            for item in data
            if isinstance(item, dict) and "name" in item and "url" in item
        ]
        return valid

    except json.JSONDecodeError:
        print(f"Warning: {path} is corrupt; starting with an empty list.")
        return []
    except OSError as e:
        print(f"Error reading {path}: {e}")
        return []





def save_products(products: List[Dict[str, Any]]) -> None:
    """Save the product list to PRODUCTS_FILE using an atomic write.

    Process:
      1) Ensure the target directory exists.
      2) Write JSON to a temp file next to the final file.
      3) Flush + fsync to push bytes to disk.
      4) Atomically replace the old file with the new one.
      Returns None; prints a message on success or errors.
    """
    path = Path(config.PRODUCTS_FILE)

    # 1) Make sure the directory exists.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare a temp file in the same directory (same filesystem is important).
    tmp = path.with_suffix(path.suffix + ".tmp")

    try:
        # 2) Write human-readable JSON to the temp file.
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(products, f, indent=4, ensure_ascii=False)

            # 3) Ensure data is physically written before replacing.
            f.flush()
            os.fsync(f.fileno())

        # 4) Replace is atomic on the same filesystem.
        os.replace(tmp, path)
        print(f"Product list saved to {path}")

    except OSError as e:
        print(f"Error saving to {path}: {e}")

        # Best-effort cleanup of the temp file (ignore if already gone).
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass



def _normalize_url(u: str) -> str:
    """Normalize a URL for duplicate checks.
    
    - Trim whitespace.
    - Require scheme and netloc; otherwise return ''.
    - Lowercase scheme and host.
    - Keep path as '' or '/', otherwise remove a trailing '/'.
    - Preserve the query string.
    """
    u = u.strip()
    p = urlparse(u)
    if not p.scheme or not p.netloc:
        return ""

    if p.path in ("", "/"):
        path = p.path
    else:
        path = p.path.rstrip("/")

    scheme = p.scheme.lower()
    host = p.netloc.lower()
    query_part = ("?" + p.query) if p.query else ""

    normalized = f"{scheme}://{host}{path}{query_part}"
    return normalized



def add_product_ui() -> None:
    """Add a new product via CLI input.

    Flow:
      1) Read product name and URL from the user (allow cancel).
      2) Validate non-empty inputs and URL structure.
      3) Check for duplicates by normalized URL.
      4) Append and persist the product list.
    """
    print("\n--- Add a New Product ---")
    try:
        product_name = input("Enter the name of the product: ").strip()
        product_url = input("Enter the URL of the product: ").strip()
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
    existing: Dict[str, Dict[str, Any]] = {}
    for p in products:
        key = _normalize_url(p.get("url", ""))
        existing[key] = p

    if normalized in existing:
        print(f"\n[Error] This URL is already being tracked as '{existing[normalized]['name']}'.")
        return

    products.append({"name": product_name, "url": product_url})
    save_products(products)
    print(f"\nSuccess! '{product_name}' has been added. Now tracking {len(products)} product(s).")


def _confirm(prompt: str) -> bool:
    """Ask a yes/no question and return True for y/yes/s/si (case-insensitive).
    
    Behavior:
      - Prompts the user and lowercases their answer.
      - Returns False on cancel (Ctrl+C/Ctrl+Z) or any non-affirmative input.
      - Default is No.
    """
    try:
        ans = input(f"{prompt} ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n[Info] Operation cancelled.")
        return False
    return ans in {"y", "yes", "s", "si"}



def delete_product_ui() -> None:
    """Delete a product selected by the user.

    Flow:
      1) Let the user pick a product (or cancel).
      2) Ask for confirmation.
      3) Remove that product (by normalized URL) and save the new list.
    """
    product_to_delete = _select_product("Select a Product to Delete")
    if not product_to_delete:
        print("[Info] Deletion cancelled.")
        return

    if not _confirm(f"Are you sure you want to delete '{product_to_delete['name']}'? (y/n):"):
        print("Deletion cancelled.")
        return

    products = load_products()
    target_norm = _normalize_url(product_to_delete.get("url", ""))

    products_after = []
    for p in products:
        current_norm = _normalize_url(p.get("url", ""))
        if current_norm != target_norm:
            products_after.append(p)

    save_products(products_after)
    print(f"'{product_to_delete['name']}' has been deleted successfully.")



def _select_product(prompt_message):
    """Display the saved products as a numbered menu and return the chosen one.

    Args:
        prompt_message (str): Message shown above the list.

    Returns:
        dict | None: The selected product dict, or None if cancelled/invalid.
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
    except (KeyboardInterrupt, EOFError):
        print("\n[Info] Selection cancelled.")
        return None
    except ValueError:
        print("\n[Error] Please enter a valid number.")
        return None

    if choice_num == 0:
        return None

    product_index = choice_num - 1
    if 0 <= product_index < len(products):
        return products[product_index]

    print("\n[Error] Invalid number.")
    return None



def view_product_history_ui():
    """Show the saved price history for a product the user selects.

    Flow:
      1) Ask the user to pick a product.
      2) Query the database for that product’s history.
      3) Print each record as [timestamp] - price - title.
      Returns None.
    """
    selected_product = _select_product("Select a Product to View History")
    if not selected_product:
        return

    product_name_to_query = selected_product["name"]
    results = database.get_product_history(product_name_to_query)

    if not results:
        print(f"\nNo history found for '{product_name_to_query}'.")
        return

    print(f"\n--- Price History for {product_name_to_query} ---")
    for row in results:
        timestamp, title, price = row
        print(f"  [{timestamp}] - {price} - {title}")

