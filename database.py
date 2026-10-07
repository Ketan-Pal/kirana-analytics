import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "kirana_store.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = OFF;")
    cursor = conn.cursor()

    # Clean legacy tables if any
    cursor.execute("DROP TABLE IF EXISTS sale_items;")
    cursor.execute("DROP TABLE IF EXISTS sales_batches;")
    cursor.execute("DROP TABLE IF EXISTS inventory_logs;")
    cursor.execute("DROP TABLE IF EXISTS items;")
    cursor.execute("DROP TABLE IF EXISTS catalog_items;")
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Product Catalog
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS catalog_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        standard_unit TEXT NOT NULL DEFAULT 'packet',
        default_price REAL NOT NULL DEFAULT 0.0,
        seasonality_tag TEXT DEFAULT 'All-Season',
        aliases TEXT DEFAULT '[]'
    );
    """)

    # 2. Daily Sales Batches
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_date TEXT NOT NULL,
        created_at TEXT NOT NULL,
        raw_json TEXT,
        items_count INTEGER DEFAULT 0,
        total_revenue REAL DEFAULT 0.0
    );
    """)

    # 3. Transaction Line Items for Patterns & Demand Forecasting
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        sale_date TEXT NOT NULL,
        month_str TEXT NOT NULL,
        day_of_week TEXT NOT NULL,
        time_period TEXT NOT NULL DEFAULT 'Evening',
        basket_id TEXT NOT NULL,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity REAL NOT NULL DEFAULT 1.0,
        unit TEXT NOT NULL DEFAULT 'packet',
        unit_price REAL NOT NULL DEFAULT 0.0,
        total_amount REAL NOT NULL DEFAULT 0.0,
        FOREIGN KEY (batch_id) REFERENCES sales_batches(id) ON DELETE CASCADE
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sale_date ON sale_items(sale_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_month_str ON sale_items(month_str);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_product ON sale_items(product_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_basket ON sale_items(basket_id);")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_FILE)
