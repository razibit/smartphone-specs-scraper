#!/usr/bin/env python3
"""
Integration test to verify price extraction is working with real data.
"""

import pytest
from smartphone_specs_scraper.scrapers.detail_scraper import DetailScraper
from smartphone_specs_scraper.utils.http_client import HTTPClient


@pytest.mark.live
def test_price_extraction_integration():
    """Test price extraction with a real phone page."""
    
    # Initialize components
    http_client = HTTPClient(delay=1.0)
    scraper = DetailScraper(http_client)
    
    # Test with a known phone URL (using the Realme Note 60x from the provided HTML)
    test_url = "https://www.mobiledokan.com/mobile/honor-x8b"
    
    print(f"Testing price extraction from: {test_url}")
    print("This may take a moment due to respectful scraping delays...\n")
    
    try:
        # Scrape the phone details
        phone_specs = scraper.scrape_phone_details(test_url)
        
        if phone_specs:
            print("✅ Successfully scraped phone details!")
            print(f"Phone: {phone_specs.brand} {phone_specs.model}")
            
            # Display price information
            print("\n📱 Price Information:")
            print(f"  Official Price: {phone_specs.price_official}")
            print(f"  Unofficial Price: {phone_specs.price_unofficial}")
            print(f"  Old Price: {phone_specs.price_old}")
            print(f"  Savings: {phone_specs.price_savings}")
            print(f"  Price Updated: {phone_specs.price_updated}")
            
            if phone_specs.price_variants:
                print(f"  Variants: {len(phone_specs.price_variants)} found")
                for variant in phone_specs.price_variants:
                    print(f"    - {variant['variant']}: {variant['price']}")
            else:
                print("  Variants: None")
                
            # Display some other key specs to verify overall scraping
            print(f"\n📋 Key Specifications:")
            print(f"  Display: {phone_specs.screen_size}")
            print(f"  RAM: {phone_specs.ram}")
            print(f"  Storage: {phone_specs.internal_storage}")
            print(f"  Battery: {phone_specs.battery_capacity}")
            print(f"  Camera: {phone_specs.primary_camera_resolution}")
            
        else:
            print("❌ Failed to scrape phone details")
            
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")

if __name__ == "__main__":
    test_price_extraction_integration()
