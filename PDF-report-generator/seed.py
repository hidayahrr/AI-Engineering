import random
import sqlite3
from datetime import datetime, timedelta

# List of mock products and customers to generate realistic data
PRODUCTS = [
    "Mechanical Keyboard",
    "Wireless Mouse",
    "UltraWide Monitor",
    "USB-C Hub",
    "Noise Canceling Headphones",
    "Ergonomic Chair",
]

CUSTOMERS = [
    "Alice Smith",
    "Bob Jones",
    "Charlie Brown",
    "Diana Prince",
    "Evan Wright",
    "Fiona Gallagher",
    "George Clark",
    "Hannah Abbott",
]


def seed_database():
    # Connects to report.db (creates the file automatically if it doesn't exist)
    conn = sqlite3.connect("report.db")
    cursor = conn.cursor()

    # Create table 'orders'
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    )

    # CRITICAL RULE: Wipe existing data so running the script twice yields exactly 200 rows
    cursor.execute("DELETE FROM orders")

    # Generate 200 random order records over the last 30 days
    now = datetime.now()
    orders = []

    for _ in range(200):
        customer = random.choice(CUSTOMERS)
        product = random.choice(PRODUCTS)
        amount = round(random.uniform(5.0, 200.0), 2)

        # Random timestamp within the last 30 days
        random_days = random.randint(0, 30)
        random_hours = random.randint(0, 23)
        order_date = now - timedelta(days=random_days, hours=random_hours)
        created_at = order_date.strftime("%Y-%m-%d %H:%M:%S")

        orders.append((customer, product, amount, created_at))

    # Insert generated records
    cursor.executemany(
        """
        INSERT INTO orders (customer, product, amount, created_at)
        VALUES (?, ?, ?, ?)
    """,
        orders,
    )

    conn.commit()

    # Query row count to verify output
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]

    conn.close()
    print(f"Database seeded successfully. Total rows in 'orders': {count}")


if __name__ == "__main__":
    seed_database()