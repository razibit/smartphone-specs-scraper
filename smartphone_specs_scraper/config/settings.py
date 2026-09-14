"""
Configuration settings for MobileDokan scraper.

Contains all constants, URLs, field mappings, and configuration parameters
used throughout the scraping process.
"""

import os
from typing import Dict, List

# Base URLs and endpoints
BASE_URL = "https://www.mobiledokan.com/mobile-category/smartphone"
DOMAIN = "https://www.mobiledokan.com"

# HTTP Client Configuration
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
]

# Request settings
REQUEST_DELAY = 1.0  # Seconds between requests
REQUEST_TIMEOUT = 30  # Request timeout in seconds
MAX_RETRIES = 3      # Maximum retry attempts
BACKOFF_FACTOR = 2   # Exponential backoff multiplier
INITIAL_BACKOFF = 1  # Initial backoff delay in seconds

# Output configuration
OUTPUT_DIR = "output"
JSON_FILENAME = "phones_data.json"
CSV_FILENAME = "phones_data.csv"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "scraper.log"

# Specification field mappings from HTML to our data model
SPEC_FIELD_MAPPINGS: Dict[str, str] = {
    # General Information
    "Brand": "brand",
    "Model": "model",
    "Device Type": "device_type",
    "Release Date": "release_date",
    "Status": "status",
    
    # Hardware & Software
    "Operating System": "operating_system",
    "OS Version": "os_version",
    "User Interface": "user_interface",
    "Chipset": "chipset",
    "CPU": "cpu",
    "CPU Cores": "cpu_cores",
    "Architecture": "architecture",
    "Fabrication": "fabrication",
    "GPU": "gpu",
    
    # Display
    "Display Type": "display_type",
    "Screen Size": "screen_size",
    "Resolution": "resolution",
    "Aspect Ratio": "aspect_ratio",
    "Pixel Density": "pixel_density",
    "Screen to Body Ratio": "screen_to_body_ratio",
    "Screen Protection": "screen_protection",
    "Bezel-less display": "bezel_less_display",
    "Touch Screen": "touch_screen",
    "Brightness": "brightness",
    "Refresh Rate": "refresh_rate",
    "Notch": "notch",
    
    # Primary Camera
    "Primary Camera Setup": "primary_camera_setup",
    "Primary Camera Resolution": "primary_camera_resolution",
    "Primary Camera Autofocus": "primary_camera_autofocus",
    "Primary Camera Flash": "primary_camera_flash",
    "Primary Camera Image Resolution": "primary_camera_image_resolution",
    "Primary Camera Settings": "primary_camera_settings",
    "Primary Camera Zoom": "primary_camera_zoom",
    "Primary Camera Shooting Modes": "primary_camera_shooting_modes",
    "Primary Camera Features": "primary_camera_features",
    "Primary Camera Video Recording": "primary_camera_video_recording",
    "Primary Camera Video FPS": "primary_camera_video_fps",
    
    # Selfie Camera
    "Selfie Camera Setup": "selfie_camera_setup",
    "Selfie Camera Resolution": "selfie_camera_resolution",
    
    # Design
    "Height": "height",
    "Width": "width",
    "Thickness": "thickness",
    "Weight": "weight",
    "Colors": "colors",
    "Waterproof": "waterproof",
    "IP Rating": "ip_rating",
    "Ruggedness": "ruggedness",
    
    # Battery
    "Battery Type": "battery_type",
    "Battery Capacity": "battery_capacity",
    "Quick Charging": "quick_charging",
    "Battery Placement": "battery_placement",
    "USB Type-C": "usb_type_c",
    
    # Memory
    "Internal Storage": "internal_storage",
    "Storage Type": "storage_type",
    "Expandable Memory": "expandable_memory",
    "USB OTG": "usb_otg",
    "RAM": "ram",
    "RAM Type": "ram_type",
    
    # Network & Connectivity
    "Network": "network",
    "SIM Slot": "sim_slot",
    "SIM Size": "sim_size",
    "EDGE": "edge",
    "GPRS": "gprs",
    "VoLTE": "volte",
    "Speed": "speed",
    "WLAN": "wlan",
    "Bluetooth": "bluetooth",
    "GPS": "gps",
    "WiFi Hotspot": "wifi_hotspot",
    "USB": "usb",
    
    # Sensors & Security
    "Sensors": "sensors",
    "Face Unlock": "face_unlock",
    
    # Multimedia
    "Loudspeaker": "loudspeaker",
    "Audio Jack": "audio_jack",
    "Video": "video",
    
    # More
    "Made by": "made_by",
    "Features": "features"
}

# Default values for missing fields
DEFAULT_VALUES: Dict[str, str] = {
    "brand": "Unknown",
    "model": "Unknown",
    "device_type": "Smartphone",
    "release_date": "Unknown",
    "status": "Unknown",
    "operating_system": "Unknown",
    "os_version": "Unknown",
    "user_interface": "Unknown",
    "chipset": "Unknown",
    "cpu": "Unknown",
    "cpu_cores": "Unknown",
    "architecture": "Unknown",
    "fabrication": "Unknown",
    "gpu": "Unknown",
    "display_type": "Unknown",
    "screen_size": "Unknown",
    "resolution": "Unknown",
    "aspect_ratio": "Unknown",
    "pixel_density": "Unknown",
    "screen_to_body_ratio": "Unknown",
    "screen_protection": "Unknown",
    "bezel_less_display": "Unknown",
    "touch_screen": "Unknown",
    "brightness": "Unknown",
    "refresh_rate": "Unknown",
    "notch": "Unknown",
    "primary_camera_setup": "Unknown",
    "primary_camera_resolution": "Unknown",
    "primary_camera_autofocus": "Unknown",
    "primary_camera_flash": "Unknown",
    "primary_camera_image_resolution": "Unknown",
    "primary_camera_settings": "Unknown",
    "primary_camera_zoom": "Unknown",
    "primary_camera_shooting_modes": "Unknown",
    "primary_camera_features": "Unknown",
    "primary_camera_video_recording": "Unknown",
    "primary_camera_video_fps": "Unknown",
    "selfie_camera_setup": "Unknown",
    "selfie_camera_resolution": "Unknown",
    "height": "Unknown",
    "width": "Unknown",
    "thickness": "Unknown",
    "weight": "Unknown",
    "colors": "Unknown",
    "waterproof": "Unknown",
    "ip_rating": "Unknown",
    "ruggedness": "Unknown",
    "battery_type": "Unknown",
    "battery_capacity": "Unknown",
    "quick_charging": "Unknown",
    "battery_placement": "Unknown",
    "usb_type_c": "Unknown",
    "internal_storage": "Unknown",
    "storage_type": "Unknown",
    "expandable_memory": "Unknown",
    "usb_otg": "Unknown",
    "ram": "Unknown",
    "ram_type": "Unknown",
    "network": "Unknown",
    "sim_slot": "Unknown",
    "sim_size": "Unknown",
    "edge": "Unknown",
    "gprs": "Unknown",
    "volte": "Unknown",
    "speed": "Unknown",
    "wlan": "Unknown",
    "bluetooth": "Unknown",
    "gps": "Unknown",
    "wifi_hotspot": "Unknown",
    "usb": "Unknown",
    "sensors": "Unknown",
    "face_unlock": "Unknown",
    "loudspeaker": "Unknown",
    "audio_jack": "Unknown",
    "video": "Unknown",
    "made_by": "Unknown",
    "features": "Unknown",
    "image_url": "",
    "detail_url": "",
    "scraped_at": ""
}

# CSS selectors and HTML parsing patterns
CSS_SELECTORS = {
    "phone_links": "a[href*='/mobile/']",
    "phone_image": "img",
    "pagination_next": "a[href*='?page=']",
    "spec_table": "table",
    "spec_row": "tr",
    "spec_label": "td:first-child",
    "spec_value": "td:last-child"
}

# JavaScript patterns for JSON extraction
JS_PATTERNS = {
    "phone_data": r'var\s+phones\s*=\s*(\[.*?\]);',
    "pagination_data": r'var\s+pagination\s*=\s*(\{.*?\});'
}

# File extensions and MIME types
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
CSV_ENCODING = 'utf-8'
JSON_ENCODING = 'utf-8'

# Error handling configuration
IGNORE_SSL_ERRORS = False
VERIFY_CERTIFICATES = True

# Progress tracking
BATCH_SIZE = 50  # Number of phones to process in each batch
PROGRESS_UPDATE_INTERVAL = 10  # Update progress every N items

def get_output_path(filename: str) -> str:
    """Get the full path for output files."""
    return os.path.join(OUTPUT_DIR, filename)

def ensure_output_directory() -> None:
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)