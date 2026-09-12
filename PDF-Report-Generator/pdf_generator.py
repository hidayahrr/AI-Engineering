import os
import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright
from db import get_report_data


def get_all_orders(db_path: str = "report.db"):
    """Fetches all 200 order rows to build a long table that spans multiple pages."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders


def generate_html_report(data: dict, all_orders: list) -> str:
    """Builds an HTML string containing structured report metrics and print CSS."""
    today_str = datetime.now().strftime("%B %d, %Y")

    # Generate rows for the top 5 products table
    top_products_rows = "".join(
        f"<tr><td>{p['product']}</td><td>${p['revenue']:,.2f}</td></tr>"
        for p in data["top_5_products"]
    )

    # Generate rows for the full 200 orders table
    all_orders_rows = "".join(
        f"<tr><td>#{o['id']}</td><td>{o['customer']}</td><td>{o['product']}</td><td>${o['amount']:,.2f}</td><td>{o['created_at']}</td></tr>"
        for o in all_orders
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sales Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                color: #333;
            }}
            h1 {{
                color: #1e293b;
                margin-bottom: 5px;
            }}
            .subtitle {{
                color: #64748b;
                font-size: 14px;
                margin-bottom: 25px;
            }}
            .metrics-grid {{
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                padding: 15px;
                border-radius: 8px;
                flex: 1;
            }}
            .metric-title {{
                font-size: 12px;
                color: #64748b;
                text-transform: uppercase;
                font-weight: bold;
            }}
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: #0f172a;
                margin-top: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}
            th, td {{
                border: 1px solid #cbd5e1;
                padding: 8px 12px;
                text-align: left;
                font-size: 12px;
            }}
            th {{
                background-color: #f1f5f9;
                font-weight: bold;
            }}
            
            /* PRINT CSS: Fixes the page-break trap */
            tr {{
                break-inside: avoid;
            }}
            thead {{
                display: table-header-group;
            }}
        </style>
    </head>
    <body>
        <h1>Executive Sales Report</h1>
        <div class="subtitle">Generated on {today_str}</div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Total Orders</div>
                <div class="metric-value">{data['total_orders']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Total Revenue</div>
                <div class="metric-value">${data['total_revenue']:,.2f}</div>
            </div>
        </div>

        <h2>Top 5 Products by Revenue</h2>
        <table>
            <thead>
                <tr>
                    <th>Product Name</th>
                    <th>Total Revenue</th>
                </tr>
            </thead>
            <tbody>
                {top_products_rows}
            </tbody>
        </table>

        <h2>All Order Transactions</h2>
        <table>
            <thead>
                <tr>
                    <th>Order ID</th>
                    <th>Customer</th>
                    <th>Product</th>
                    <th>Amount</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
                {all_orders_rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_content


def render_pdf(output_path: str = "reports/test.pdf") -> str:
    """Executes the pipeline: queries data, renders HTML, and prints to PDF using Playwright."""
    os.makedirs("reports", exist_ok=True)

    # 1. Query aggregated metrics and raw order rows
    report_data = get_report_data()
    all_orders = get_all_orders()

    # 2. Build HTML string
    html_content = generate_html_report(report_data, all_orders)

    # 3. Render PDF via Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content)
        page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"}
        )
        browser.close()

    print(f"PDF successfully rendered to {output_path}")
    return output_path


if __name__ == "__main__":
    render_pdf()