# Design Document

## Overview

The source-site scraper is designed as a modular Python application that systematically extracts smartphone data from example.com. The system follows a three-phase approach: URL discovery, data extraction, and data storage. The architecture emphasizes reliability, maintainability, and respectful scraping practices.

Based on analysis of the HTML structure, the scraper will handle:
- Paginated smartphone listings with JSON data embedded in JavaScript
- Individual phone detail pages with structured specification tables
- Dynamic content loading and various HTML structures
- Error handling for missing or malformed data

## Architecture

The scraper follows a modular architecture with clear separation of concerns:

```
smartphone_specs_scraper/
├── main.py                 # Entry point and orchestration
├── scrapers/
│   ├── __init__.py
│   ├── listing_scraper.py  # Handles category page scraping
│   ├── detail_scraper.py   # Handles individual phone scraping
│   └── base_scraper.py     # Common scraping functionality
├── models/
│   ├── __init__.py
│   └── phone_data.py       # Data models and validation
├── utils/
│   ├── __init__.py
│   ├── http_client.py      # HTTP request handling
│   ├── parser.py           # HTML parsing utilities
│   └── file_manager.py     # File I/O operations
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration constants
└── output/                 # Generated data files
    ├── phones_data.json
    └── phones_data.csv
```

## Components and Interfaces

### 1. HTTP Client (`utils/http_client.py`)
Handles all HTTP communications with proper headers, delays, and error handling.

**Interface:**
```python
class HTTPClient:
    def __init__(self, delay: float = 1.0, timeout: int = 30)
    def get(self, url: str, retries: int = 3) -> requests.Response
    def get_with_backoff(self, url: str) -> requests.Response
```

**Key Features:**
- User-Agent rotation
- Request delays (1-2 seconds between requests)
- Exponential backoff for rate limiting
- Timeout handling
- Retry logic with configurable attempts

### 2. Listing Scraper (`scrapers/listing_scraper.py`)
Extracts smartphone URLs from category pages and handles pagination.

**Interface:**
```python
class ListingScraper:
    def __init__(self, http_client: HTTPClient)
    def scrape_all_phone_urls(self, base_url: str) -> List[Dict[str, str]]
    def extract_phone_urls_from_page(self, html: str) -> List[Dict[str, str]]
    def get_next_page_url(self, html: str, current_page: int) -> Optional[str]
```

**Key Features:**
- Extracts embedded JSON data from JavaScript variables
- Handles pagination detection and navigation
- Filters out ads and non-mobile links
- Extracts phone URLs and thumbnail images

### 3. Detail Scraper (`scrapers/detail_scraper.py`)
Extracts comprehensive specifications from individual phone pages.

**Interface:**
```python
class DetailScraper:
    def __init__(self, http_client: HTTPClient)
    def scrape_phone_details(self, phone_url: str) -> Dict[str, Any]
    def extract_specifications(self, soup: BeautifulSoup) -> Dict[str, Any]
    def extract_price_information(self, soup: BeautifulSoup) -> Dict[str, Any]
    def parse_specification_table(self, soup: BeautifulSoup) -> Dict[str, str]
```

**Key Features:**
- Parses structured specification tables
- Extracts comprehensive price information (official, unofficial, variants, discounts)
- Handles missing or malformed data gracefully
- Extracts all required specification categories
- Normalizes data formats and units

### 4. Data Models (`models/phone_data.py`)
Defines the structure and validation for phone data.

**Interface:**
```python
@dataclass
class PhoneSpecifications:
    # General Information
    brand: Optional[str] = None
    model: Optional[str] = None
    device_type: Optional[str] = None
    release_date: Optional[str] = None
    status: Optional[str] = None
    
    # Pricing Information
    price_official: Optional[str] = None
    price_unofficial: Optional[str] = None
    price_old: Optional[str] = None
    price_savings: Optional[str] = None
    price_variants: Optional[List[Dict[str, str]]] = None
    price_updated: Optional[str] = None
    
    # Hardware & Software
    operating_system: Optional[str] = None
    os_version: Optional[str] = None
    # ... (all other specification fields)
    
    def to_dict(self) -> Dict[str, Any]
    def validate(self) -> bool
```

### 5. File Manager (`utils/file_manager.py`)
Handles data persistence in JSON and CSV formats.

**Interface:**
```python
class FileManager:
    def save_to_json(self, data: List[Dict], filename: str) -> None
    def save_to_csv(self, data: List[Dict], filename: str) -> None
    def create_output_directory(self) -> None
    def generate_filename(self, base_name: str, extension: str) -> str
```

## Price Extraction Strategy

### Price Structure Analysis
Based on the provided HTML samples, source-site uses several price patterns:

1. **Official + Unofficial Prices**: Both prices displayed with tags
2. **Official Price Only**: Single official price with tag
3. **Unofficial Price Only**: Single unofficial price with tag  
4. **Discounted Prices**: Old price crossed out, new price, savings amount/percentage
5. **Multiple Variants**: Dropdown with different storage/RAM configurations and prices

### Price Extraction Logic
```python
def extract_price_information(self, soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract all price-related information from phone detail page
    Handles multiple price formats and variant configurations
    """
    price_data = {
        'price_official': None,
        'price_unofficial': None,
        'price_old': None,
        'price_savings': None,
        'price_variants': [],
        'price_updated': None
    }
    
    # Extract from .price-and-variant container
    # Handle official prices with (Official) tag
    # Handle unofficial prices with (Unofficial) tag
    # Extract old prices from .old-price elements
    # Parse variant prices from .varcont lists
    # Extract update date from .updat elements
```

### Price Parsing Patterns
- **Official Price**: `৳.43,999 (Official)` → Extract numeric value and tag
- **Unofficial Price**: `৳.50,000 (Unofficial)` → Extract numeric value and tag
- **Old Price**: `<span class="old-price h6">৳30,999</span>` → Extract crossed-out price
- **Savings**: `৳1,000 (3.23% off)` → Extract amount and percentage
- **Variants**: Extract from variant dropdown and price list combinations

## Data Models

### Phone Specification Structure
Based on the requirements, each phone record contains:

```python
{
    # General
    "brand": str,
    "model": str,
    "device_type": str,
    "release_date": str,
    "status": str,
    
    # Pricing
    "price_official": str,
    "price_unofficial": str,
    "price_old": str,
    "price_savings": str,
    "price_variants": list,  # List of variant prices and specs
    "price_updated": str,
    
    # Hardware & Software
    "operating_system": str,
    "os_version": str,
    "user_interface": str,
    "chipset": str,
    "cpu": str,
    "cpu_cores": str,
    "architecture": str,
    "fabrication": str,
    "gpu": str,
    
    # Display
    "display_type": str,
    "screen_size": str,
    "resolution": str,
    "aspect_ratio": str,
    "pixel_density": str,
    "screen_to_body_ratio": str,
    "screen_protection": str,
    "bezel_less_display": str,
    "touch_screen": str,
    "brightness": str,
    "refresh_rate": str,
    "notch": str,
    
    # Cameras
    "primary_camera_setup": str,
    "primary_camera_resolution": str,
    "primary_camera_autofocus": str,
    "primary_camera_flash": str,
    "primary_camera_image_resolution": str,
    "primary_camera_settings": str,
    "primary_camera_zoom": str,
    "primary_camera_shooting_modes": str,
    "primary_camera_features": str,
    "primary_camera_video_recording": str,
    "primary_camera_video_fps": str,
    "selfie_camera_setup": str,
    "selfie_camera_resolution": str,
    
    # Design
    "height": str,
    "width": str,
    "thickness": str,
    "weight": str,
    "colors": str,
    "waterproof": str,
    "ip_rating": str,
    "ruggedness": str,
    
    # Battery
    "battery_type": str,
    "battery_capacity": str,
    "quick_charging": str,
    "battery_placement": str,
    "usb_type_c": str,
    
    # Memory
    "internal_storage": str,
    "storage_type": str,
    "expandable_memory": str,
    "usb_otg": str,
    "ram": str,
    "ram_type": str,
    
    # Network & Connectivity
    "network": str,
    "sim_slot": str,
    "sim_size": str,
    "edge": str,
    "gprs": str,
    "volte": str,
    "speed": str,
    "wlan": str,
    "bluetooth": str,
    "gps": str,
    "wifi_hotspot": str,
    "usb": str,
    
    # Sensors & Security
    "sensors": str,
    "face_unlock": str,
    
    # Multimedia
    "loudspeaker": str,
    "audio_jack": str,
    "video": str,
    
    # More
    "made_by": str,
    "features": str,
    
    # Metadata
    "image_url": str,
    "detail_url": str,
    "scraped_at": str
}
```

## Error Handling

### HTTP Error Handling
- **Connection Errors**: Retry with exponential backoff
- **Timeout Errors**: Configurable timeout with retry logic
- **Rate Limiting**: Detect 429 responses and implement backoff
- **404 Errors**: Log and continue with remaining URLs
- **Server Errors (5xx)**: Retry with increasing delays

### Parsing Error Handling
- **Missing Elements**: Use default values and log warnings
- **Malformed HTML**: Skip problematic sections and continue
- **Encoding Issues**: Handle different character encodings
- **JavaScript Parsing**: Fallback to HTML parsing if JSON extraction fails

### Data Validation
- **Required Fields**: Validate presence of critical fields
- **Data Types**: Ensure proper type conversion
- **Format Validation**: Validate dates, numbers, and structured data
- **Duplicate Detection**: Identify and handle duplicate entries

## Testing Strategy

### Unit Testing
- **HTTP Client**: Mock requests and test retry logic
- **Parsers**: Test with sample HTML files
- **Data Models**: Validate data structure and conversion
- **File Operations**: Test JSON/CSV generation

### Integration Testing
- **End-to-End Flow**: Test complete scraping workflow
- **Error Scenarios**: Test handling of various error conditions
- **Data Integrity**: Verify scraped data accuracy
- **Performance**: Test with large datasets

### Test Data
- **Sample HTML Files**: Store representative pages for testing
- **Mock Responses**: Create mock HTTP responses for different scenarios
- **Expected Outputs**: Define expected results for validation

### Testing Framework
```python
# Test structure
tests/
├── unit/
│   ├── test_http_client.py
│   ├── test_listing_scraper.py
│   ├── test_detail_scraper.py
│   └── test_data_models.py
├── integration/
│   ├── test_full_workflow.py
│   └── test_error_handling.py
├── fixtures/
│   ├── sample_listing_page.html
│   ├── sample_detail_page.html
│   └── expected_outputs.json
└── conftest.py
```

## Configuration Management

### Settings Structure
```python
# config/settings.py
BASE_URL = "https://example.com/mobile-category/smartphone"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    # Additional user agents for rotation
]

REQUEST_DELAY = 1.0  # Seconds between requests
REQUEST_TIMEOUT = 30  # Request timeout in seconds
MAX_RETRIES = 3      # Maximum retry attempts
BACKOFF_FACTOR = 2   # Exponential backoff multiplier

OUTPUT_DIR = "output"
JSON_FILENAME = "phones_data.json"
CSV_FILENAME = "phones_data.csv"

# Specification field mappings
SPEC_FIELD_MAPPINGS = {
    "Brand": "brand",
    "Model": "model",
    "Device Type": "device_type",
    # ... additional mappings
}
```

## Performance Considerations

### Optimization Strategies
- **Connection Pooling**: Reuse HTTP connections
- **Concurrent Processing**: Use threading for I/O-bound operations
- **Memory Management**: Process data in batches for large datasets
- **Caching**: Cache parsed data to avoid re-processing

### Scalability
- **Batch Processing**: Process phones in configurable batch sizes
- **Progress Tracking**: Implement progress indicators and resumption
- **Resource Monitoring**: Monitor memory and CPU usage
- **Rate Limiting**: Respect server resources with appropriate delays

### Monitoring and Logging
```python
# Logging configuration
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
```

This design provides a robust, maintainable, and respectful web scraping solution that can handle the complexities of the source-site website while producing clean, structured data for analysis.