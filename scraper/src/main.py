import os
import requests

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
TARGET_URL = "https://books.toscrape.com/catalogue/page-1.html"
CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "catalogue-page-1.html")

# Honest User-Agent header identifying the project
HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/your-username/your-repo)"
}


def fetch_page_1():
    """
    Fetches the first catalogue page of Books to Scrape.
    If a local cached copy exists, reads from disk.
    Otherwise, makes a polite HTTP GET request and saves the HTML to disk.
    """
    # 1. Check if the file is already cached locally
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            html_content = f.read()
        file_size = len(html_content.encode("utf-8"))
        print(f"CACHE HIT: Read {file_size} bytes from {CACHE_FILE}")
        return html_content

    # 2. If not cached, fetch from live server
    print(f"FETCH: Requesting {TARGET_URL}...")
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=10)
        
        # Verify HTTP status code
        if response.status_code != 200:
            print(f"ERROR: Received HTTP status code {response.status_code}")
            return None

        html_content = response.text
        
        # Save the fetched HTML to local cache
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        file_size = len(html_content.encode("utf-8"))
        print(f"FETCH SUCCESS: Saved {file_size} bytes to {CACHE_FILE}")
        return html_content

    except requests.RequestException as e:
        print(f"NETWORK ERROR: Failed to fetch page. Details: {e}")
        return None


if __name__ == "__main__":
    fetch_page_1()