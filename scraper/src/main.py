import os
import re
import json
import time
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
CATALOGUE_PAGES = [
    "https://books.toscrape.com/catalogue/page-1.html",
    "https://books.toscrape.com/catalogue/page-2.html",
    "https://books.toscrape.com/catalogue/page-3.html",
]

# Controlled failure testing: Add one fake URL to test page isolation
FAKE_TEST_URL = "https://books.toscrape.com/catalogue/this-page-does-not-exist_9999/index.html"

CACHE_DIR = "cache"
OUTPUT_DIR = "output"
BOOKS_FILE = os.path.join(OUTPUT_DIR, "books.json")
ERRORS_FILE = os.path.join(OUTPUT_DIR, "errors.json")
REPORT_FILE = os.path.join(OUTPUT_DIR, "run-report.json")

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

# ------------------------------------------------------------------------------
# Global Metrics Counter for Reporting
# ------------------------------------------------------------------------------
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
# Resilient HTTP Fetcher with Selective Retries & Caching
# ------------------------------------------------------------------------------

def get_cached_filename(url: str) -> str:
    clean_name = url.replace("https://", "").replace("http://", "").replace("/", "_")
    return os.path.join(CACHE_DIR, f"{clean_name}.html")


def fetch_with_retry_and_cache(url: str, delay_seconds: float = 1.0) -> str | None:
    """
    Fetches HTML content with caching.
    Retries once on timeouts or 5xx server errors.
    Does NOT retry on 404 (Not Found) or 403 (Forbidden).
    """
    cache_file = get_cached_filename(url)

    # 1. Check local cache
    if os.path.exists(cache_file):
        METRICS["cache_hits"] += 1
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    # 2. Live HTTP Request
    time.sleep(delay_seconds)
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        try:
            METRICS["pages_fetched_live"] += 1
            response = requests.get(url, headers=HEADERS, timeout=10)

            # Do not retry on 404 or 403
            if response.status_code in (403, 404):
                print(f"[FETCH ERROR] Permanent HTTP {response.status_code} for {url}. Skipping.")
                METRICS["failed_pages"] += 1
                return None

            # Retry on server errors (5xx)
            if response.status_code >= 500:
                print(f"[SERVER ERROR] HTTP {response.status_code} on attempt {attempt}/{max_attempts} for {url}")
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

        except requests.Timeout:
            print(f"[TIMEOUT] Request timed out on attempt {attempt}/{max_attempts} for {url}")
            if attempt < max_attempts:
                time.sleep(2.0)
                continue
            METRICS["failed_pages"] += 1
            return None

        except requests.RequestException as e:
            print(f"[NETWORK ERROR] Failed to fetch {url}: {e}")
            METRICS["failed_pages"] += 1
            return None

    METRICS["failed_pages"] += 1
    return None


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
# Page Parsing & Extraction
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
# Main Pipeline Execution
# ------------------------------------------------------------------------------

def run_pipeline():
    start_time_utc = datetime.now(timezone.utc)
    start_timestamp = start_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    start_perf = time.perf_counter()

    print("--- STAGE 5: FAULT TOLERANCE & REPORTING ---")

    unique_urls = set()
    validated_records = []
    error_records = []

    # 1. Discover URLs from catalogue pages
    for cat_url in CATALOGUE_PAGES:
        urls = extract_book_urls(cat_url)
        for url in urls:
            unique_urls.add(url)

    # Inject one intentionally invalid fake URL for fault-tolerance verification
    unique_urls.add(FAKE_TEST_URL)

    print(f"Total target URLs to process (including 1 fake URL): {len(unique_urls)}")

    # 2. Process each book independently
    for url in unique_urls:
        try:
            record_dict = parse_and_normalize_book(product_url=url, source_page=CATALOGUE_PAGES[0])

            if not record_dict:
                error_records.append({"url": url, "reason": "HTTP fetch failed or invalid HTML structure"})
                continue

            # Validate against Pydantic model
            validated_model = BookRecord(**record_dict)
            validated_records.append(validated_model.model_dump(mode="json"))

        except ValidationError as ve:
            error_records.append({
                "url": url,
                "reason": "Schema validation failed",
                "details": ve.errors()
            })
        except Exception as ex:
            # Global catch to isolate and survive any unexpected exceptions
            error_records.append({
                "url": url,
                "reason": f"Unhandled exception: {str(ex)}"
            })

    # 3. Store valid output to output/books.json
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(validated_records, f, indent=2, ensure_ascii=False)

    # 4. Store error output to output/errors.json
    with open(ERRORS_FILE, "w", encoding="utf-8") as f:
        json.dump(error_records, f, indent=2, ensure_ascii=False)

    # 5. Generate and write output/run-report.json
    end_perf = time.perf_counter()
    duration_seconds = round(end_perf - start_perf, 2)

    run_report = {
        "start_time": start_timestamp,
        "duration_seconds": duration_seconds,
        "total_urls_discovered": len(unique_urls),
        "pages_fetched_live": METRICS["pages_fetched_live"],
        "cache_hits": METRICS["cache_hits"],
        "valid_records": len(validated_records),
        "invalid_records": len(error_records),
        "failed_pages": METRICS["failed_pages"]
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(run_report, f, indent=2)

    # 6. Terminal Summary Report
    print("\n================ RUN REPORT SUMMARY ================")
    print(f"Start Time         : {run_report['start_time']}")
    print(f"Duration           : {run_report['duration_seconds']}s")
    print(f"Valid Records      : {run_report['valid_records']} -> {BOOKS_FILE}")
    print(f"Invalid Records    : {run_report['invalid_records']} -> {ERRORS_FILE}")
    print(f"Failed Pages       : {run_report['failed_pages']}")
    print(f"Report File        : {REPORT_FILE}")
    print("===================================================\n")


if __name__ == "__main__":
    run_pipeline()