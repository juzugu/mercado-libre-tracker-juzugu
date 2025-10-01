# database.py
import sqlite3
from . import config

REQUIRED_FIELDS = ("timestamp", "product_name", "scraped_title", "price", "price_numeric", "status")

def connect():
    """Create a connection with sane defaults for WAL workloads."""
    conn = sqlite3.connect(config.DB_FILE, timeout=5)  # wait up to 5s if busy
    conn.execute("PRAGMA busy_timeout=3000;")          # extra safety against SQLITE_BUSY
    conn.execute("PRAGMA synchronous=NORMAL;")         # balance speed/durability
    return conn
# Add this function inside database.py

def get_latest_price(product_name):
    """Gets the most recent PriceNumeric for a product."""
    with connect() as connection:
        cursor = connection.execute(
            "SELECT PriceNumeric FROM prices WHERE ProductName = ? ORDER BY Timestamp DESC LIMIT 1",
            (product_name,),
        )
        result = cursor.fetchone() # Fetches only one row
    
    if result:
        return result[0] # result is a tuple like (199.99,), so we take the first item
    return None # Return None if no history exists

def initialize():
    """Create DB/table/index and enable WAL (persistent)."""
    with connect() as connection:
        c = connection.cursor()
        c.execute("PRAGMA journal_mode=WAL;")  # WAL is persistent
        c.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                Timestamp    TEXT,
                ProductName  TEXT,
                ScrapedTitle TEXT,
                Price        TEXT,
                PriceNumeric REAL,
                Status       TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_prices_product_ts ON prices(ProductName, Timestamp)")
    print("Database initialized.")

def save_price_data(data):
    """Insert one price row."""
    for k in REQUIRED_FIELDS:
        if k not in data:
            raise ValueError(f"Missing field '{k}' in data")
    with connect() as connection:
        connection.execute(
            "INSERT INTO prices (Timestamp, ProductName, ScrapedTitle, Price, PriceNumeric, Status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                data["timestamp"],
                data["product_name"],
                data["scraped_title"],
                data["price"],
                data["price_numeric"],
                data["status"],
            ),
        )

def get_product_history(product_name):
    """Newest-first history for a product."""
    with connect() as connection:
        cur = connection.execute(
            "SELECT Timestamp, ScrapedTitle, Price "
            "FROM prices WHERE ProductName = ? ORDER BY Timestamp DESC",
            (product_name,),
        )
        return cur.fetchall()
