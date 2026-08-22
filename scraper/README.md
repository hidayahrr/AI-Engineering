# Web Scraper — Books to Scrape

## Target Classification

- **Target Site**: Books to Scrape (`https://books.toscrape.com/`)
- **Site Type**: Sandbox (A website explicitly built for developers to practice web scraping).
- **Scope**: The first 3 catalogue pages (60 books total) and their individual detail pages.
- **Data Collected**: Book Title, Price (GBP), Availability/Stock Status, Star Rating, Description, and Source Page URL.
- **Robots.txt Result**: No `robots.txt` file found (`404 Not Found`).
- **Ethics Statement**: I will not reuse this code on another site without checking its rules and terms first.

## Lane & Environment Setup

- **Language & Runtime**: Python 3.10+
- **HTTP Client**: `requests`
- **HTML Parser**: `BeautifulSoup` (`bs4`)
- **Schema Validator**: `pydantic`

### Installation & Execution

1. Clone the repository and navigate to the scraper folder:
   ```bash
   git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
   cd "AI Engineering/scraper"
   ```

2. Create and activate a virtual environment:

   Bash
   ```
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install required dependencies:

   Bash
   ```
   pip install -r requirements.txt
   ```

4. Run the scraper pipeline:

   Bash
   ```
   python src/main.py
   ```

## Politeness Rules

1. **Honest User-Agent**: Every request identifies the scraper:

   `FlyRankInternship-A9/1.0 (+https://github.com/your-username/your-repo)`
2. **Politeness Delay**: Enforces a `1.0` second delay between live network requests.
3. **Timeout**: Enforces a strict `10` second timeout per request to prevent hung connections.
4. **Local Caching**: HTML pages are cached in `cache/` so subsequent runs do not hit the live server.
5. **Selective Retries**: Retries once on timeouts or `5xx` server errors; skips immediately without retrying on `404` or `403` errors.

## Record Schema (Pydantic Model)

Every extracted record is strictly validated against the following schema before storage:

| **Field Name**      | **Type**  | **Description**                                      | **Required?** |
| ------------------- | --------- | ---------------------------------------------------- | ------------- |
| `title`             | `str`     | Product title                                        | **Yes**       |
| `product_url`       | `HttpUrl` | Canonical product URL                                | **Yes**       |
| `price_text`        | `str`     | Raw price string (e.g., `"£51.77"`)                  | **Yes**       |
| `price_gbp`         | `float`   | Parsed numerical price in GBP (`> 0`)                | **Yes**       |
| `availability_text` | `str`     | Raw stock string (e.g., `"In stock (22 available)"`) | **Yes**       |
| `in_stock`          | `bool`    | Stock availability flag                              | **Yes**       |
| `stock_count`       | `int`     | Parsed available quantity (`>= 0`)                   | **Yes**       |
| `rating_text`       | `str`     | Raw rating word (e.g., `"Three"`)                    | Optional      |
| `rating`            | `int`     | Numerical rating (`1` to `5`)                        | Optional      |
| `description`       | `str`     | Book summary                                         | Optional      |
| `source_page`       | `HttpUrl` | Catalogue URL where item was discovered              | **Yes**       |
| `fetched_at`        | `str`     | UTC ISO-8601 timestamp                               | **Yes**       |

## Execution Proof (`output/run-report.json`)

JSON

```
{
  "start_time": "2026-08-22T11:03:49Z",
  "duration_seconds": 0.15,
  "total_urls_discovered": 61,
  "pages_fetched_live": 1,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 1,
  "failed_pages": 1
}
```

### Why No Headless Browser Was Used

This target website serves pure static HTML directly from the server. All product titles, prices, ratings, and descriptions are fully rendered in the raw HTTP response body. Using a browser automation framework (e.g., Selenium or Playwright) would introduce unnecessary CPU overhead, slow down execution speed, and consume significantly more memory without adding any value.

## Technical Limitations

- **Pagination Hardcoding**: The current implementation explicitly targets the first 3 catalogue pages. It does not dynamically parse the "Next" button pagination links to traverse the full site automatically.
- **Static Content Assumption**: The scraper relies on standard `requests` and assumes the server returns static HTML without JavaScript-rendered dynamic content.

## Ethics Note

1. **Use Official APIs First**: Always prefer official REST or GraphQL APIs over web scraping when available.
2. **Respect Access Controls**: Never attempt to bypass authentication logins, paywalls, CAPTCHAs, or IP blocks.
3. **Data Minimization**: Collect only the specific fields necessary for your application, and never store private personal data without consent.