# MobileDokan Scraper

MobileDokan Scraper is a Python tool for collecting smartphone listing URLs and detailed specifications from the public MobileDokan website. It follows listing pagination, parses product detail pages, validates records, and exports timestamped JSON and CSV files.

> This project is intended for education, research, and personal analysis. Use it responsibly, follow the source site's terms and `robots.txt`, keep the configured request delay, and comply with applicable law.

## What it does

- discovers smartphone URLs from MobileDokan category pages;
- follows pagination and filters advertisements/non-phone links;
- extracts general, pricing, hardware, display, camera, design, battery, memory, connectivity, sensor, multimedia, and feature fields;
- retries transient HTTP failures with delays and exponential backoff;
- continues past malformed or incomplete records when possible; and
- writes consistent timestamped JSON and CSV exports.

## Requirements

- Python 3.9 or newer;
- internet access for live scraping; and
- permission to access and process the source pages.

## Install

Create a virtual environment and install the project with its development tools:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

For a runtime-only installation, use `python -m pip install -r requirements.txt`. The development requirements are in `requirements-dev.txt`.

## Run the scraper

The default command scrapes the configured smartphone category and writes results to `output/`:

```bash
python main.py
```

Use a small bounded run while developing or checking source-site changes:

```bash
python main.py --max-phones 10
python main.py --start-page 2 --max-phones 10
python main.py --output-dir ./data --log-level DEBUG
python main.py --base-url https://www.mobiledokan.com/mobile-category/smartphone
```

Available options:

| Option | Purpose | Default |
| --- | --- | --- |
| `--max-phones N` | Limit the number of phones processed | all available |
| `--start-page N` | Start listing pagination at page `N` | `1` |
| `--output-dir PATH` | Choose the export directory | `output` |
| `--base-url URL` | Override the smartphone category URL | configured MobileDokan URL |
| `--log-level LEVEL` | Use `DEBUG`, `INFO`, `WARNING`, or `ERROR` logging | `INFO` |

Generated exports are named like `phones_data_YYYYMMDD_HHMMSS.json` and `phones_data_YYYYMMDD_HHMMSS.csv`. Logs are written to `scraper.log`; generated exports and logs are ignored by Git.

## Use the library

The package can also be used from Python:

```python
from mobiledokan_scraper.config.settings import BASE_URL
from mobiledokan_scraper.main import MobileDokanScraper

scraper = MobileDokanScraper(output_dir="output")
result = scraper.run_complete_scraping(
    base_url=BASE_URL,
    max_phones=10,
)

print(result["statistics"])
```

For lower-level control, `ListingScraper`, `DetailScraper`, `HTTPClient`, and `FileManager` are available in their respective package modules.

## Configuration

Runtime constants live in [`mobiledokan_scraper/config/settings.py`](mobiledokan_scraper/config/settings.py), including:

- source URLs and selectors;
- request timeout, delay, retry, and backoff settings;
- output filenames and encodings;
- specification field mappings and fallback values; and
- logging and progress settings.

The CLI currently exposes safe URL, pagination, output, and log-level overrides. Change request behavior in the settings module or through a small wrapper rather than reducing the default delay for a large run.

## Development and tests

Run the deterministic local checks from the repository root:

```bash
python -m compileall -q main.py mobiledokan_scraper tests
python -m pytest
python -m pytest --cov=mobiledokan_scraper --cov-report=term-missing
```

The default test command uses local HTML fixtures and mocks. The live price-extraction check is deliberately opt-in because it makes real requests and depends on the current source site:

```bash
python -m pytest -m live
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution and validation expectations.

## Repository layout

```text
.
├── .github/                    # CI, Dependabot, issue forms, PR template
├── docs/                       # Usage and exported-data documentation
├── mobiledokan_scraper/        # Installable scraper package
│   ├── config/                 # URLs, selectors, and runtime settings
│   ├── models/                 # Phone dataclass and validation
│   ├── scrapers/               # Listing and detail parsers
│   └── utils/                  # HTTP, logging, errors, and file exports
├── tests/                      # Unit tests and fixture-backed integration tests
├── output/                     # Local generated exports; ignored except for .gitkeep
├── main.py                     # Command-line entry point
├── pyproject.toml              # Packaging, CLI, pytest, and coverage metadata
├── requirements.txt            # Runtime dependencies
└── requirements-dev.txt        # Runtime plus test dependencies
```

The captured HTML pages and fixture files are kept as local parsing examples. They represent snapshots, not guaranteed current source-site behavior.

## Documentation

- [Usage guide](docs/usage.md)
- [Exported data structure](docs/data_structure.md)
- [Documentation index](docs/README.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)

## License

This project is available under the [MIT License](LICENSE).

