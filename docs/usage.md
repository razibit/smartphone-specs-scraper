# Usage guide

This guide covers the supported command-line workflow and the lower-level Python components.

## Quick start

From the repository root, install the project and run a bounded scrape first:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python main.py --max-phones 10
```

The command discovers listing URLs, requests each detail page, validates the records, and writes JSON and CSV files under `output/`.

## Command-line options

```text
python main.py [OPTIONS]

--max-phones N       Maximum number of phones to process; default is all found.
--start-page N       Listing page to start from; default is 1.
--output-dir PATH    Destination for generated JSON and CSV files; default is output.
--base-url URL       Smartphone category URL to scrape.
--log-level LEVEL    DEBUG, INFO, WARNING, or ERROR; default is INFO.
```

Examples:

```bash
python main.py --max-phones 5
python main.py --start-page 3 --max-phones 25
python main.py --output-dir ./data --log-level DEBUG
```

For a shell-independent entry point after installation, use:

```bash
mobiledokan-scraper --max-phones 10
```

## Configuration

Edit [`mobiledokan_scraper/config/settings.py`](../mobiledokan_scraper/config/settings.py) to change:

- `BASE_URL` and `DOMAIN`;
- `REQUEST_DELAY`, `REQUEST_TIMEOUT`, `MAX_RETRIES`, and backoff values;
- JSON/CSV output names and encodings;
- HTML selectors and embedded-JavaScript patterns; and
- logging, batching, and progress settings.

Keep a meaningful delay between requests. A source-site change should be handled by updating the relevant selector or parser and adding a fixture-backed regression test.

## Programmatic workflow

Use the orchestrator when you want the same URL-discovery, detail-scraping, validation, and export behavior as the CLI:

```python
from mobiledokan_scraper.config.settings import BASE_URL
from mobiledokan_scraper.main import MobileDokanScraper

scraper = MobileDokanScraper(output_dir="output")
result = scraper.run_complete_scraping(
    base_url=BASE_URL,
    max_phones=10,
    start_page=1,
)

if result["success"]:
    print(result["export_results"]["files"])
else:
    print(result["error"] or "Scrape did not produce any valid records")
```

The lower-level components can be composed when the full orchestrator is not needed:

```python
from mobiledokan_scraper.config.settings import BASE_URL
from mobiledokan_scraper.scrapers.detail_scraper import DetailScraper
from mobiledokan_scraper.scrapers.listing_scraper import ListingScraper
from mobiledokan_scraper.utils.file_manager import FileManager
from mobiledokan_scraper.utils.http_client import HTTPClient

with HTTPClient(delay=1.0) as client:
    listing = ListingScraper(client)
    detail = DetailScraper(client)
    phones = []

    for phone in listing.scrape_all_phone_urls(BASE_URL)[:10]:
        record = detail.scrape_phone_details(
            phone["detail_url"],
            phone.get("image_url", ""),
        )
        if record and record.validate():
            phones.append(record)

FileManager("output").save_phone_specifications(phones)
```

## Output files

Each successful run creates:

- `phones_data_YYYYMMDD_HHMMSS.json` — a list of structured phone records;
- `phones_data_YYYYMMDD_HHMMSS.csv` — a flat, spreadsheet-friendly version; and
- `scraper.log` — progress, warning, and error messages.

The default `output/` directory and `scraper.log` are ignored by Git. Move any dataset you intentionally want to publish into a documented, reviewed sample-data location rather than committing a routine run.

See [`data_structure.md`](data_structure.md) for fields and examples.

## Testing

The default suite is deterministic and does not make live network requests:

```bash
python -m compileall -q main.py mobiledokan_scraper tests
python -m pytest
```

Coverage:

```bash
python -m pytest --cov=mobiledokan_scraper --cov-report=term-missing
```

The live price check is marked `live` and must be requested explicitly:

```bash
python -m pytest -m live
```

Live checks can fail when the source is unavailable or its HTML changes. They should not be used as the only validation for parser changes; update local fixtures and deterministic tests as well.

## Troubleshooting

### Imports fail after a fresh checkout

Install the project in editable mode from the repository root:

```bash
python -m pip install -e ".[dev]"
```

Running tests with `python -m pytest` also ensures the repository root is on the import path.

### No records are exported

Run a small request with `--log-level DEBUG`, inspect `scraper.log`, and confirm that the source page is reachable. If the page structure changed, compare it with the fixtures and update the relevant parser plus tests.

### Requests are slow or rate-limited

This scraper intentionally waits between requests and retries transient failures. Increase `REQUEST_DELAY` and avoid parallel requests when the source is under load.

### Missing fields

Missing fields are represented as `null` in JSON and empty cells in CSV. A missing field is not necessarily a parser failure; compare the source page, the field mapping, and the exported record before changing fallback behavior.

