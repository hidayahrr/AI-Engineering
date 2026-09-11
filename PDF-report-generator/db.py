import sqlite3
from typing import Any, Dict


def get_report_data(db_path: str = "report.db") -> Dict[str, Any]:
    """Queries report.db and returns aggregated metrics as a dictionary."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enables access to columns by name
    cursor = conn.cursor()

    # Query 1: Total Number of Orders
    cursor.execute("SELECT COUNT(*) AS total_orders FROM orders")
    total_orders = cursor.fetchone()["total_orders"]

    # Query 2: Total Revenue
    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total_revenue FROM orders")
    total_revenue = round(cursor.fetchone()["total_revenue"], 2)

    # Query 3: Top 5 Products by Revenue
    cursor.execute(
        """
        SELECT product, ROUND(SUM(amount), 2) AS revenue
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
    """
    )
    top_5_products = [dict(row) for row in cursor.fetchall()]

    # Query 4: Orders per day for the last 7 days
    cursor.execute(
        """
        SELECT DATE(created_at) AS order_date, COUNT(*) AS order_count
        FROM orders
        WHERE created_at >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY order_date ASC
    """
    )
    orders_last_7_days = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_5_products": top_5_products,
        "orders_last_7_days": orders_last_7_days,
    }