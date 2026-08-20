import os
import time
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

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
HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/your-username/your-repo)"
}


# ------------------------------------------------------------------------------
# Helper Functions: Politeness & Caching
# ------------------------------------------------------------------------------

def get_cached_filename(url: str) -> str:
    """Generates a safe local filename from a URL for caching."""
    clean_name = url.replace("https://", "").replace("http://", "").replace("/", "_")
    return os.path.join(CACHE_DIR, f"{clean_name}.html")


def fetch_with_cache(url: str, delay_seconds: float = 1.0) -> str | None:
    """
    Fetches a URL using local disk caching.
    If not cached, sleeps for `delay_seconds` before sending a polite HTTP request.
    """
    cache_file = get_cached_filename(url)

    # 1. Check local cache
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    # 2. Enforce politeness delay before live fetch
    time.sleep(delay_seconds)

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"ERROR: Received HTTP {response.status_code} for {url}")
            return None

        html_content = response.text

        # Save to cache
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_content

    except requests.RequestException as e:
        print(f"NETWORK ERROR fetching {url}: {e}")
        return None


# ------------------------------------------------------------------------------
# Extraction Logic
# ------------------------------------------------------------------------------

def extract_book_urls(catalogue_url: str) -> list[str]:
    """Extracts all 20 book detail page URLs from a single catalogue page."""
    html = fetch_with_cache(catalogue_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    book_links = []

    # Target product containers on catalogue page
    articles = soup.find_all("article", class_="product_pod")
    for article in articles:
        a_tag = article.find("h3").find("a")
        if a_tag and "href" in a_tag.attrs:
            relative_url = a_tag["href"]
            # Convert relative URL (e.g. 'a-light-in-the-attic_1000/index.html') to absolute
            absolute_url = urljoin(BASE_URL, relative_url)
            book_links.append(absolute_url)

    return book_links


def parse_book_detail(product_url: str, source_page: str) -> dict | None:
    """Parses a single book detail page and returns raw un-normalized fields."""
    html = fetch_with_cache(product_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Scope selectors strictly to the primary product container
    product_main = soup.find("div", class_="product_main")
    if not product_main:
        return None

    # Title
    h1_tag = product_main.find("h1")
    title = h1_tag.get_text(strip=True) if h1_tag else None

    # Price string
    price_tag = product_main.find("p", class_="price_color")
    price_text = price_tag.get_text(strip=True) if price_tag else None

    # Availability string
    availability_tag = product_main.find("p", class_="instock availability")
    availability_text = (
        availability_tag.get_text(strip=True) if availability_tag else None
    )

    # Star Rating class string (e.g., class="star-rating Three")
    rating_tag = product_main.find("p", class_="star-rating")
    rating_text = None
    if rating_tag and "class" in rating_tag.attrs:
        # Extract class name that isn't 'star-rating' (e.g., 'Three')
        classes = [c for c in rating_tag["class"] if c != "star-rating"]
        if classes:
            rating_text = classes[0]

    # Description (Optional field - handle missing case with None)
    desc_header = soup.find("div", id="product_description")
    description = None
    if desc_header:
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            description = desc_p.get_text(strip=True)

    # Provenance metadata
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


# ------------------------------------------------------------------------------
# Execution Pipeline
# ------------------------------------------------------------------------------

def run_stage_3():
    all_raw_records = []
    seen_urls = set()

    print("--- STAGE 3: EXTRACTING BOOK DETAILS ---")

    # Iterate through catalogue pages 1 to 3
    for cat_url in CATALOGUE_PAGES:
        print(f"Collecting book URLs from catalogue: {cat_url}")
        book_urls = extract_book_urls(cat_url)

        for url in book_urls:
            seen_urls.add(url)
            record = parse_book_detail(product_url=url, source_page=cat_url)
            if record:
                all_raw_records.append(record)

    # Output Checkpoint Results
    print("\n================ CHECKPOINT REPORT ================")
    print(f"Total Unique URLs Collected : {len(seen_urls)}")
    print(f"Total Raw Records Extracted : {len(all_raw_records)}")
    print("===================================================\n")

    if all_raw_records:
        print("SAMPLE RAW RECORD (Record #1):")
        import json
        print(json.dumps(all_raw_records[0], indent=2))


if __name__ == "__main__":
    run_stage_3()