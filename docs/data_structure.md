# Data Structure Documentation

This document describes the complete data structure of the scraped phone information from example.com.

## Overview

Each phone record contains comprehensive specifications organized into the following categories:

- General Information
- Pricing Information
- Hardware & Software
- Display
- Cameras
- Design
- Battery
- Memory
- Network & Connectivity
- Sensors & Security
- Multimedia
- Additional Information
- Metadata

## Field Definitions

### General Information

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `brand` | string | Phone manufacturer | "Samsung", "Apple", "Xiaomi" |
| `model` | string | Phone model name | "Galaxy S24 Ultra", "iPhone 15 Pro" |
| `device_type` | string | Type of device | "Smartphone", "Feature Phone" |
| `release_date` | string | Release date | "January 2024", "Q2 2023" |
| `status` | string | Availability status | "Available", "Upcoming", "Discontinued" |

### Pricing Information

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `price_official` | string | Official price in BDT | "43,999", "14,999" |
| `price_unofficial` | string | Unofficial/market price in BDT | "44,000", "25,000" |
| `price_old` | string | Previous/original price (for discounts) | "30,999" |
| `price_savings` | string | Discount amount and percentage | "৳1,000 (3.23% off)" |
| `price_variants` | array | List of variant prices and specifications | `[{"variant": "512GB", "price": "43,999"}]` |
| `price_updated` | string | Price last updated date | "June 6, 2025", "July 15, 2025" |

### Hardware & Software

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `operating_system` | string | Operating system | "Android", "iOS" |
| `os_version` | string | OS version | "v14", "17.2" |
| `user_interface` | string | Custom UI layer | "One UI 6.1", "MIUI 14" |
| `chipset` | string | Processor chipset | "Qualcomm Snapdragon 8 Gen 3" |
| `cpu` | string | CPU details | "Octa-core (1x3.39 GHz Cortex-X4...)" |
| `cpu_cores` | string | Number of CPU cores | "8 Cores", "6 Cores" |
| `architecture` | string | CPU architecture | "64 bit", "32 bit" |
| `fabrication` | string | Manufacturing process | "4 nm", "7 nm" |
| `gpu` | string | Graphics processor | "Adreno 750", "Apple GPU" |

### Display

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `display_type` | string | Display technology | "Dynamic AMOLED 2X", "Super Retina XDR" |
| `screen_size` | string | Screen diagonal size | "6.8 inches", "6.1 inches" |
| `resolution` | string | Screen resolution | "3120 x 1440 pixels" |
| `aspect_ratio` | string | Screen aspect ratio | "19.3:9", "19.5:9" |
| `pixel_density` | string | Pixels per inch | "501 ppi", "460 ppi" |
| `screen_to_body_ratio` | string | Screen-to-body percentage | "89.9%", "87.4%" |
| `screen_protection` | string | Screen protection type | "Corning Gorilla Glass Victus 2" |
| `bezel_less_display` | string | Bezel-less design | "Yes", "No" |
| `touch_screen` | string | Touch screen type | "Capacitive Touchscreen, Multi-touch" |
| `brightness` | string | Maximum brightness | "2600 nits", "1000 nits" |
| `refresh_rate` | string | Screen refresh rate | "120 Hz", "60 Hz" |
| `notch` | string | Notch/cutout type | "Punch-hole", "Dynamic Island", "Notch" |

### Cameras

#### Primary Camera

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `primary_camera_setup` | string | Camera configuration | "Quad Camera", "Triple Camera" |
| `primary_camera_resolution` | string | Camera megapixels | "200+50+12+10MP", "48+12+12MP" |
| `primary_camera_autofocus` | string | Autofocus type | "Phase Detection Autofocus" |
| `primary_camera_flash` | string | Flash type | "LED Flash", "True Tone Flash" |
| `primary_camera_image_resolution` | string | Maximum image size | "16384x12288 Pixels" |
| `primary_camera_settings` | string | Camera settings | "Exposure compensation, ISO control" |
| `primary_camera_zoom` | string | Zoom capabilities | "100x Space Zoom", "5x Optical Zoom" |
| `primary_camera_shooting_modes` | string | Available shooting modes | "High-res mode, Night mode, Portrait mode" |
| `primary_camera_features` | string | Camera features | "Optical Image Stabilization, HDR" |
| `primary_camera_video_recording` | string | Video recording specs | "8K@30fps, 4K@60fps" |
| `primary_camera_video_fps` | string | Video frame rates | "960 fps", "240 fps" |

#### Selfie Camera

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `selfie_camera_setup` | string | Front camera configuration | "Single Camera", "Dual Camera" |
| `selfie_camera_resolution` | string | Front camera megapixels | "12MP", "32MP" |

### Design

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `height` | string | Phone height | "162.3 mm", "147.6 mm" |
| `width` | string | Phone width | "79.0 mm", "71.6 mm" |
| `thickness` | string | Phone thickness | "8.6 mm", "7.8 mm" |
| `weight` | string | Phone weight | "232 grams", "187 grams" |
| `colors` | string | Available colors | "Titanium Black, Titanium Gray, Titanium Violet" |
| `waterproof` | string | Water resistance | "Water resistant", "Splash resistant" |
| `ip_rating` | string | IP protection rating | "IP68", "IP67" |
| `ruggedness` | string | Durability features | "Dust proof", "Shock resistant" |

### Battery

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `battery_type` | string | Battery technology | "Li-Ion", "Li-Po" |
| `battery_capacity` | string | Battery capacity | "5000 mAh", "3279 mAh" |
| `quick_charging` | string | Fast charging specs | "45W Super Fast Charging", "20W Fast Charging" |
| `battery_placement` | string | Battery type | "Non-removable", "Removable" |
| `usb_type_c` | string | USB-C support | "Yes", "No" |

### Memory

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `internal_storage` | string | Built-in storage | "256 GB", "128 GB" |
| `storage_type` | string | Storage technology | "UFS 4.0", "NVMe" |
| `expandable_memory` | string | MicroSD support | "Yes", "No" |
| `usb_otg` | string | USB OTG support | "Yes", "No" |
| `ram` | string | System memory | "12 GB", "8 GB" |
| `ram_type` | string | RAM technology | "LPDDR5X", "LPDDR5" |

### Network & Connectivity

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `network` | string | Supported networks | "5G, 4G, 3G, 2G" |
| `sim_slot` | string | SIM configuration | "Dual SIM", "Single SIM" |
| `sim_size` | string | SIM card size | "Nano SIM", "eSIM" |
| `edge` | string | EDGE support | "Yes", "No" |
| `gprs` | string | GPRS support | "Yes", "No" |
| `volte` | string | VoLTE support | "Yes", "No" |
| `speed` | string | Data speeds | "HSPA 42.2/5.76 Mbps, LTE-A" |
| `wlan` | string | WiFi specifications | "Wi-Fi 802.11 a/b/g/n/ac/ax, dual band" |
| `bluetooth` | string | Bluetooth version | "v5.3, A2DP, LE" |
| `gps` | string | GPS capabilities | "Yes, with A-GPS, GLONASS, BDS, GALILEO" |
| `wifi_hotspot` | string | Hotspot support | "Yes", "No" |
| `usb` | string | USB specifications | "USB Type-C 3.2", "Lightning" |

### Sensors & Security

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `sensors` | string | Available sensors | "Accelerometer, Gyro, Proximity, Compass" |
| `face_unlock` | string | Face unlock support | "Yes", "No" |

### Multimedia

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `loudspeaker` | string | Speaker configuration | "Yes, with stereo speakers" |
| `audio_jack` | string | 3.5mm jack support | "Yes", "No" |
| `video` | string | Video codec support | "H.265/HEVC, H.264/AVC" |

### Additional Information

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `made_by` | string | Manufacturer | "Samsung", "Apple" |
| `features` | string | Special features | "S Pen support, Samsung DeX, Wireless charging" |

### Metadata

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `image_url` | string | Product image URL | "https://example.com/wp-content/uploads/..." |
| `detail_url` | string | Product page URL | "https://example.com/samsung-galaxy-s24-ultra/" |
| `scraped_at` | string | Scraping timestamp | "2024-01-15T10:30:45" |

## Data Types

- **string**: Text data, may contain null values for missing information
- **null**: Explicitly null values for missing or unavailable data

## Missing Data Handling

When information is not available on the source page:
- Fields are set to `null` in JSON format
- Fields are left empty in CSV format
- No placeholder text is inserted

## Data Validation

The scraper includes validation for:
- Required fields (brand, model, device_type)
- Data format consistency
- URL validation for image and detail URLs
- Timestamp format validation

## Export Formats

### JSON Format
- Complete nested structure
- Null values preserved
- UTF-8 encoding
- Pretty-printed for readability

### CSV Format
- Flat structure with all fields as columns
- Empty cells for null values
- UTF-8 encoding with BOM for Excel compatibility
- Headers included in first row

## Usage Examples

### Loading JSON Data (Python)
```python
import json

with open('phones_data.json', 'r', encoding='utf-8') as f:
    phones = json.load(f)

for phone in phones:
    print(f"{phone['brand']} {phone['model']}")
```

### Loading CSV Data (Python)
```python
import pandas as pd

df = pd.read_csv('phones_data.csv')
print(df[['brand', 'model', 'battery_capacity']].head())
```

### Loading CSV Data (Excel)
1. Open Excel
2. Go to Data > Get Data > From File > From Text/CSV
3. Select the CSV file
4. Choose UTF-8 encoding
5. Import the data

This data structure provides comprehensive information about smartphones from example.com, suitable for analysis, comparison, and research purposes.