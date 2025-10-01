import sqlite3
from typing import Dict, Any, Optional, Iterable, Tuple
try:
    from . import config  # package-relative
except ImportError:       # script execution fallback
    import config

REQUIRED_FIELDS = ("timestamp", "product_name", "scraped_title", "price", "price_numeric", "status")

def connect() -> sqlite3.Connection:
    """Create a connection with sane defaults for WAL-like workloads."""
    conn = sqlite3.connect(config.DB_FILE, timeout=5)  # wait up to 5s if busy
    conn.execute("PRAGMA busy_timeout=3000;")          # extra safety against SQLITE_BUSY
    conn.execute("PRAGMA synchronous=NORMAL;")         # balance speed/durability
    return conn

def initialize() -> None:
    """Ensure the table exists."""
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                Timestamp    TEXT NOT NULL,
                ProductName  TEXT NOT NULL,
                ScrapedTitle TEXT,
                Price        TEXT,
                PriceNumeric REAL,
                Status       TEXT
            )
            """
        )

def save_price_data(data: Dict[str, Any]) -> None:
    """Insert one scraped record. Requires REQUIRED_FIELDS keys."""
    missing = [k for k in REQUIRED_FIELDS if k not in data]
    if missing:
        raise ValueError(f"save_price_data missing required fields: {missing}")
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO prices (Timestamp, ProductName, ScrapedTitle, Price, PriceNumeric, Status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["timestamp"],
                data["product_name"],
                data.get("scraped_title"),
                data.get("price"),
                data.get("price_numeric"),
                data.get("status"),
            ),
        )

def get_latest_price(product_name: str) -> Optional[float]:
    """Return the most recent PriceNumeric for a product, or None."""
    with connect() as connection:
        cur = connection.execute(
            """
            SELECT PriceNumeric FROM prices
            WHERE ProductName = ?
            ORDER BY Timestamp DESC
            LIMIT 1
            """,
            (product_name,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return row[0]

def get_product_history(product_name: str) -> Iterable[Tuple[str, str, str]]:
    """Newest-first history for a product: (Timestamp, ScrapedTitle, Price)."""
    with connect() as connection:
        cur = connection.execute(
            """
            SELECT Timestamp, ScrapedTitle, Price
            FROM prices
            WHERE ProductName = ?
            ORDER BY Timestamp DESC
            """,
            (product_name,),
        )
        return cur.fetchall()
