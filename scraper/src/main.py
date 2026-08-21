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

CACHE_DIR = "cache"
OUTPUT_DIR = "output"
BOOKS_FILE = os.path.join(OUTPUT_DIR, "books.json")
ERRORS_FILE = os.path.join(OUTPUT_DIR, "errors.json")

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
# Pydantic Schema Definition
# ------------------------------------------------------------------------------

class BookRecord(BaseModel):
    """Schema defining the required types and constraints for a clean book record."""
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
# Helper & Politeness Functions
# ------------------------------------------------------------------------------

def get_cached_filename(url: str) -> str:
    clean_name = url.replace("https://", "").replace("http://", "").replace("/", "_")
    return os.path.join(CACHE_DIR, f"{clean_name}.html")


def fetch_with_cache(url: str, delay_seconds: float = 1.0) -> str | None:
    cache_file = get_cached_filename(url)

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    time.sleep(delay_seconds)

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None

        html_content = response.text
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_content

    except requests.RequestException:
        return None


# ------------------------------------------------------------------------------
# Data Normalization
# ------------------------------------------------------------------------------

def normalize_price(price_text: Optional[str]) -> Optional[float]:
    """Extracts numeric float from price string (e.g., '£51.77' -> 51.77)."""
    if not price_text:
        return None
    match = re.search(r"[\d.]+", price_text)
    return float(match.group(0)) if match else None


def normalize_availability(availability_text: Optional[str]) -> tuple[bool, int]:
    """Parses stock availability string (e.g., 'In stock (22 available)' -> (True, 22))."""
    if not availability_text:
        return False, 0

    in_stock = "In stock" in availability_text
    match = re.search(r"\d+", availability_text)
    stock_count = int(match.group(0)) if match else (1 if in_stock else 0)
    return in_stock, stock_count


def normalize_rating(rating_text: Optional[str]) -> Optional[int]:
    """Converts word ratings to integers (e.g., 'Three' -> 3)."""
    if not rating_text:
        return None
    return WORD_TO_NUM.get(rating_text)


# ------------------------------------------------------------------------------
# Extraction & Parsing Logic
# ------------------------------------------------------------------------------

def extract_book_urls(catalogue_url: str) -> list[str]:
    html = fetch_with_cache(catalogue_url)
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
    html = fetch_with_cache(product_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    product_main = soup.find("div", class_="product_main")
    if not product_main:
        return None

    # Raw extractions
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

    # Normalization steps
    price_gbp = normalize_price(price_text)
    in_stock, stock_count = normalize_availability(availability_text)
    rating = normalize_rating(rating_text)

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "price_gbp": price_gbp,
        "availability_text": availability_text,
        "in_stock": in_stock,
        "stock_count": stock_count,
        "rating_text": rating_text,
        "rating": rating,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


# ------------------------------------------------------------------------------
# Main Pipeline: Run, Validate, Store
# ------------------------------------------------------------------------------

def run_pipeline():
    print("--- STAGE 4: NORMALIZE, VALIDATE & STORE ---")

    unique_urls = set()
    validated_records = []
    error_records = []

    # 1. Scrape catalogue pages
    for cat_url in CATALOGUE_PAGES:
        print(f"Fetching links from: {cat_url}")
        urls = extract_book_urls(cat_url)
        for url in urls:
            unique_urls.add(url)

    print(f"Discovered {len(unique_urls)} unique book URLs across 3 catalogue pages.")

    # 2. Extract, normalize, and validate each book (using unique_urls for idempotency)
    for url in unique_urls:
        # Determine source page reference
        source_page = CATALOGUE_PAGES[0] # Default fallback
        record_dict = parse_and_normalize_book(product_url=url, source_page=source_page)

        if not record_dict:
            error_records.append({"url": url, "error": "Failed to parse product page"})
            continue

        # Validate against Pydantic schema
        try:
            validated_model = BookRecord(**record_dict)
            # Convert validated Pydantic model to Python dictionary (with HttpUrl exported as string)
            validated_records.append(validated_model.model_dump(mode="json"))
        except ValidationError as ve:
            error_records.append({
                "record": record_dict,
                "error": ve.errors()
            })

    # 3. Store valid output to output/books.json
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(validated_records, f, indent=2, ensure_ascii=False)

    # 4. Store any failed records to output/errors.json
    with open(ERRORS_FILE, "w", encoding="utf-8") as f:
        json.dump(error_records, f, indent=2, ensure_ascii=False)

    # 5. Print Summary Report
    print("\n================ FINAL SUMMARY REPORT ================")
    print(f"Total Unique URLs Discovered : {len(unique_urls)}")
    print(f"Valid Records Saved          : {len(validated_records)} -> {BOOKS_FILE}")
    print(f"Failed/Rejected Records      : {len(error_records)} -> {ERRORS_FILE}")
    print("======================================================\n")


if __name__ == "__main__":
    run_pipeline()