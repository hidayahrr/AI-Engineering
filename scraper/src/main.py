import os
import re
import csv
import json
import time
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin
from typing import Optional

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, Field, ValidationError

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
BASE_URL = "https://books.toscrape.com/catalogue/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
CATALOGUE_PAGES = [
    "https://books.toscrape.com/catalogue/page-1.html",
    "https://books.toscrape.com/catalogue/page-2.html",
    "https://books.toscrape.com/catalogue/page-3.html",
]

FAKE_TEST_URL = "https://books.toscrape.com/catalogue/this-page-does-not-exist_9999/index.html"

CACHE_DIR = "cache"
OUTPUT_DIR = "output"

BOOKS_JSON_FILE = os.path.join(OUTPUT_DIR, "books.json")
BOOKS_CSV_FILE = os.path.join(OUTPUT_DIR, "books.csv")
ERRORS_FILE = os.path.join(OUTPUT_DIR, "errors.json")
REPORT_FILE = os.path.join(OUTPUT_DIR, "run-report.json")
CHANGES_FILE = os.path.join(OUTPUT_DIR, "changes.json")
DASHBOARD_FILE = os.path.join(OUTPUT_DIR, "dashboard.html")
PREVIOUS_STATE_FILE = os.path.join(CACHE_DIR, "previous_state.json")

HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/your-username/your-repo)"
}

WORD_TO_NUM = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}

METRICS = {
    "pages_fetched_live": 0,
    "cache_hits": 0,
    "failed_pages": 0
}


# ------------------------------------------------------------------------------
# Pydantic Schema Definition
# ------------------------------------------------------------------------------

class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float = Field(gt=0, description="Price in GBP, must be greater than 0")
    availability_text: str
    in_stock: bool
    stock_count: int = Field(ge=0, description="Available inventory count")
    rating_text: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Star rating between 1 and 5")
    description: Optional[str] = None
    source_page: HttpUrl
    fetched_at: str


# ------------------------------------------------------------------------------
# Resilient HTTP Fetcher
# ------------------------------------------------------------------------------

def get_cached_filename(url: str) -> str:
    clean_name = url.replace("https://", "").replace("http://", "").replace("/", "_")
    return os.path.join(CACHE_DIR, f"{clean_name}.html")


def fetch_with_retry_and_cache(url: str, delay_seconds: float = 1.0) -> str | None:
    cache_file = get_cached_filename(url)

    if os.path.exists(cache_file):
        METRICS["cache_hits"] += 1
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    time.sleep(delay_seconds)
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        try:
            METRICS["pages_fetched_live"] += 1
            response = requests.get(url, headers=HEADERS, timeout=10)

            if response.status_code in (403, 404):
                METRICS["failed_pages"] += 1
                return None

            if response.status_code >= 500:
                if attempt < max_attempts:
                    time.sleep(2.0)
                    continue
                METRICS["failed_pages"] += 1
                return None

            if response.status_code == 200:
                html_content = response.text
                os.makedirs(CACHE_DIR, exist_ok=True)
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                return html_content

        except requests.RequestException:
            if attempt < max_attempts:
                time.sleep(2.0)
                continue
            METRICS["failed_pages"] += 1
            return None

    METRICS["failed_pages"] += 1
    return None


# ------------------------------------------------------------------------------
# Stage 2: Dynamic Catalogue Discovery
# ------------------------------------------------------------------------------

def discover_catalogue_pages(start_url: str, max_pages: int = 3) -> tuple[list[str], list[str], int]:
    """
    Crawls catalogue pages dynamically by following the 'next' pagination link.
    Returns (discovered_catalogue_urls, discovered_book_urls, total_raw_count).
    """
    current_page_url = start_url
    catalogue_pages = []
    all_book_urls = []

    while current_page_url and len(catalogue_pages) < max_pages:
        catalogue_pages.append(current_page_url)
        html = fetch_with_retry_and_cache(current_page_url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        articles = soup.find_all("article", class_="product_pod")
        for article in articles:
            a_tag = article.find("h3").find("a")
            if a_tag and "href" in a_tag.attrs:
                relative_url = a_tag["href"]
                absolute_url = urljoin(BASE_URL, relative_url)
                all_book_urls.append(absolute_url)

        next_li = soup.find("li", class_="next")
        if next_li and next_li.find("a"):
            next_href = next_li.find("a")["href"]
            current_page_url = urljoin(current_page_url, next_href)
        else:
            current_page_url = None

    return catalogue_pages, all_book_urls, len(all_book_urls)


# ------------------------------------------------------------------------------
# Data Normalization
# ------------------------------------------------------------------------------

def normalize_price(price_text: Optional[str]) -> Optional[float]:
    if not price_text:
        return None
    match = re.search(r"[\d.]+", price_text)
    return float(match.group(0)) if match else None


def normalize_availability(availability_text: Optional[str]) -> tuple[bool, int]:
    if not availability_text:
        return False, 0
    in_stock = "In stock" in availability_text
    match = re.search(r"\d+", availability_text)
    stock_count = int(match.group(0)) if match else (1 if in_stock else 0)
    return in_stock, stock_count


def normalize_rating(rating_text: Optional[str]) -> Optional[int]:
    if not rating_text:
        return None
    return WORD_TO_NUM.get(rating_text)


# ------------------------------------------------------------------------------
# Parsing Logic
# ------------------------------------------------------------------------------

def extract_book_urls(catalogue_url: str) -> list[str]:
    html = fetch_with_retry_and_cache(catalogue_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    book_links = []
    articles = soup.find_all("article", class_="product_pod")

    for article in articles:
        a_tag = article.find("h3").find("a")
        if a_tag and "href" in a_tag.attrs:
            relative_url = a_tag["href"]
            absolute_url = urljoin(BASE_URL, relative_url)
            book_links.append(absolute_url)

    return book_links


def parse_and_normalize_book(product_url: str, source_page: str) -> dict | None:
    html = fetch_with_retry_and_cache(product_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    product_main = soup.find("div", class_="product_main")
    if not product_main:
        return None

    h1_tag = product_main.find("h1")
    title = h1_tag.get_text(strip=True) if h1_tag else ""

    price_tag = product_main.find("p", class_="price_color")
    price_text = price_tag.get_text(strip=True) if price_tag else ""

    availability_tag = product_main.find("p", class_="instock availability")
    availability_text = availability_tag.get_text(strip=True) if availability_tag else ""

    rating_tag = product_main.find("p", class_="star-rating")
    rating_text = None
    if rating_tag and "class" in rating_tag.attrs:
        classes = [c for c in rating_tag["class"] if c != "star-rating"]
        if classes:
            rating_text = classes[0]

    desc_header = soup.find("div", id="product_description")
    description = None
    if desc_header:
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            description = desc_p.get_text(strip=True)

    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "price_gbp": normalize_price(price_text),
        "availability_text": availability_text,
        "in_stock": normalize_availability(availability_text)[0],
        "stock_count": normalize_availability(availability_text)[1],
        "rating_text": rating_text,
        "rating": normalize_rating(rating_text),
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


# ------------------------------------------------------------------------------
# Extra 1: CSV Export with Value Flattening
# ------------------------------------------------------------------------------

def export_to_csv(records: list[dict]):
    """
    Exports validated records to output/books.csv.
    Flattens missing/None values into empty strings and normalizes line breaks.
    """
    if not records:
        return

    fieldnames = list(records[0].keys())

    with open(BOOKS_CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            flattened_row = {}
            for key, val in record.items():
                if val is None:
                    flattened_row[key] = ""
                elif isinstance(val, str):
                    flattened_row[key] = val.replace("\r", " ").replace("\n", " ")
                else:
                    flattened_row[key] = val
            writer.writerow(flattened_row)


# ------------------------------------------------------------------------------
# Extra 2: Change Detection (Hashing State)
# ------------------------------------------------------------------------------

def compute_record_hash(record: dict) -> str:
    """Computes a SHA-256 hash of core content fields to detect modifications."""
    core_content = {
        "title": record["title"],
        "price_gbp": record["price_gbp"],
        "stock_count": record["stock_count"],
        "rating": record["rating"],
        "description": record["description"]
    }
    encoded = json.dumps(core_content, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def perform_change_detection(current_records: list[dict]) -> dict:
    """
    Compares current records against previous execution state stored in cache.
    Categorizes URLs into: new, changed, unchanged, or gone.
    """
    previous_state = {}
    if os.path.exists(PREVIOUS_STATE_FILE):
        try:
            with open(PREVIOUS_STATE_FILE, "r", encoding="utf-8") as f:
                previous_state = json.load(f)
        except Exception:
            previous_state = {}

    current_state = {}
    changes = {
        "new": [],
        "changed": [],
        "unchanged": [],
        "gone": []
    }

    for record in current_records:
        url = record["product_url"]
        record_hash = compute_record_hash(record)
        current_state[url] = record_hash

        if url not in previous_state:
            changes["new"].append(url)
        elif previous_state[url] != record_hash:
            changes["changed"].append(url)
        else:
            changes["unchanged"].append(url)

    for url in previous_state:
        if url not in current_state:
            changes["gone"].append(url)

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(PREVIOUS_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(current_state, f, indent=2)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CHANGES_FILE, "w", encoding="utf-8") as f:
        json.dump(changes, f, indent=2)

    return changes


# ------------------------------------------------------------------------------
# Extra 3: Tiny HTML Dashboard Generation
# ------------------------------------------------------------------------------

def generate_html_dashboard(run_report: dict, records: list[dict], changes: dict):
    """Generates a standalone HTML dashboard visualizing pipeline health and stats."""
    prices = [r["price_gbp"] for r in records if r.get("price_gbp")]
    min_price = min(prices) if prices else 0.0
    max_price = max(prices) if prices else 0.0
    avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scraper Observability Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f6f8; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ margin-top: 0; color: #111; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .card {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 15px; text-align: center; }}
        .card .number {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-top: 5px; }}
        .badge-success {{ background: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-size: 14px; display: inline-block; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ border: 1px solid #dee2e6; padding: 10px; text-align: left; }}
        th {{ background: #f1f3f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Book Scraper Dashboard</h1>
        <p><span class="badge-success">Status: Healthy</span> &nbsp; <strong>Freshness (UTC):</strong> {run_report['start_time']}</p>
        
        <div class="grid">
            <div class="card">
                <div>Total Records</div>
                <div class="number">{run_report['valid_records']}</div>
            </div>
            <div class="card">
                <div>Failed Pages</div>
                <div class="number" style="color: #dc3545;">{run_report['failed_pages']}</div>
            </div>
            <div class="card">
                <div>Duration</div>
                <div class="number">{run_report['duration_seconds']}s</div>
            </div>
            <div class="card">
                <div>Avg Price</div>
                <div class="number">£{avg_price}</div>
            </div>
        </div>

        <h2>Price Metrics</h2>
        <ul>
            <li><strong>Min Price:</strong> £{min_price}</li>
            <li><strong>Max Price:</strong> £{max_price}</li>
            <li><strong>Average Price:</strong> £{avg_price}</li>
        </ul>

        <h2>Change Detection Summary</h2>
        <table>
            <tr><th>State</th><th>Count</th></tr>
            <tr><td>New Records</td><td>{len(changes['new'])}</td></tr>
            <tr><td>Changed Records</td><td>{len(changes['changed'])}</td></tr>
            <tr><td>Unchanged Records</td><td>{len(changes['unchanged'])}</td></tr>
            <tr><td>Gone Records</td><td>{len(changes['gone'])}</td></tr>
        </table>
    </div>
</body>
</html>
"""
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)


# ------------------------------------------------------------------------------
# Main Pipeline
# ------------------------------------------------------------------------------

def run_pipeline():
    start_time_utc = datetime.now(timezone.utc)
    start_timestamp = start_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    start_perf = time.perf_counter()

    print("--- STAGE 2: DISCOVER THREE CATALOGUE PAGES ---")

    # Dynamic catalogue discovery for Stage 2
    cat_pages, discovered_urls, raw_count = discover_catalogue_pages(START_URL, max_pages=3)
    unique_urls = set(discovered_urls)

    # Stage 2 Checkpoint Log
    print(f"catalogue_pages={len(cat_pages)}, discovered={raw_count}, unique_urls={len(unique_urls)}")

    # Add failure test URL for resilience testing
    processing_urls = set(unique_urls)
    processing_urls.add(FAKE_TEST_URL)

    validated_records = []
    error_records = []

    for url in processing_urls:
        try:
            record_dict = parse_and_normalize_book(product_url=url, source_page=cat_pages[0])

            if not record_dict:
                error_records.append({"url": url, "reason": "HTTP fetch failed or invalid HTML structure"})
                continue

            validated_model = BookRecord(**record_dict)
            validated_records.append(validated_model.model_dump(mode="json"))

        except ValidationError as ve:
            error_records.append({
                "url": url,
                "reason": "Schema validation failed",
                "details": ve.errors()
            })
        except Exception as ex:
            error_records.append({
                "url": url,
                "reason": f"Unhandled exception: {str(ex)}"
            })

    # Save JSON Outputs
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(BOOKS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(validated_records, f, indent=2, ensure_ascii=False)

    with open(ERRORS_FILE, "w", encoding="utf-8") as f:
        json.dump(error_records, f, indent=2, ensure_ascii=False)

    # Execute Extras
    export_to_csv(validated_records)
    changes = perform_change_detection(validated_records)

    end_perf = time.perf_counter()
    duration_seconds = round(end_perf - start_perf, 2)

    run_report = {
        "start_time": start_timestamp,
        "duration_seconds": duration_seconds,
        "total_urls_discovered": len(processing_urls),
        "pages_fetched_live": METRICS["pages_fetched_live"],
        "cache_hits": METRICS["cache_hits"],
        "valid_records": len(validated_records),
        "invalid_records": len(error_records),
        "failed_pages": METRICS["failed_pages"]
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(run_report, f, indent=2)

    generate_html_dashboard(run_report, validated_records, changes)

    print("\n================ FINAL REPORT ================")
    print(f"Valid Records Saved : {len(validated_records)} -> {BOOKS_JSON_FILE}")
    print(f"CSV Export          : {BOOKS_CSV_FILE}")
    print(f"Change Detection    : {CHANGES_FILE}")
    print(f"HTML Dashboard      : {DASHBOARD_FILE}")
    print("==============================================\n")


if __name__ == "__main__":
    run_pipeline()