"""
Integration tests for data validation and accuracy.

This module tests the accuracy of scraped data against known fixtures
and validates data consistency across different formats.
"""

import pytest
import json
import csv
from pathlib import Path
from unittest.mock import Mock, patch

from mobiledokan_scraper.main import MobileDokanScraper
from mobiledokan_scraper.models.phone_data import PhoneSpecifications
from mobiledokan_scraper.scrapers.listing_scraper import ListingScraper
from mobiledokan_scraper.scrapers.detail_scraper import DetailScraper
from mobiledokan_scraper.utils.http_client import HTTPClient


class TestDataValidation:
    """Test data validation and accuracy against known fixtures."""
    
    def test_listing_data_extraction_accuracy(self, sample_fixtures, expected_data):
        """Test accuracy of listing data extraction."""
        # Create mock HTTP client
        mock_client = Mock(spec=HTTPClient)
        mock_response = Mock()
        mock_response.text = sample_fixtures['sample_listing_page']
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        
        # Create listing scraper and extract data
        listing_scraper = ListingScraper(mock_client)
        phone_urls = listing_scraper.extract_phone_urls_from_page(sample_fixtures['sample_listing_page'])
        
        # Validate extracted data
        assert len(phone_urls) >= 2, "Should extract at least 2 phones from fixture"
        
        # Check first phone data
        first_phone = phone_urls[0]
        assert 'detail_url' in first_phone
        assert 'image_url' in first_phone
        assert 'title' in first_phone
        
        # Validate specific expected data from fixture
        phone_titles = [phone.get('title', '') for phone in phone_urls]
        assert any('Infinix Smart 8 Pro' in title for title in phone_titles)
        assert any('Google Pixel 7' in title for title in phone_titles)
    
    def test_detail_data_extraction_accuracy(self, sample_fixtures, expected_data):
        """Test accuracy of detail data extraction."""
        # Create mock HTTP client with proper response
        mock_client = Mock(spec=HTTPClient)
        
        # Create a proper mock response that works with requests
        mock_response = Mock()
        mock_response.text = sample_fixtures['sample_detail_page']
        mock_response.content = sample_fixtures['sample_detail_page'].encode('utf-8')  # Add content attribute
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()  # Add this method
        mock_client.get.return_value = mock_response
        
        # Create detail scraper and extract data
        detail_scraper = DetailScraper(mock_client)
        phone_specs = detail_scraper.scrape_phone_details(
            "https://www.mobiledokan.com/realme-note-60x",
            "image_url.jpg"
        )
        
        # Validate extracted specifications
        assert phone_specs is not None
        
        # Check against expected data from fixture
        expected_realme = expected_data[0]  # First item is Realme Note 60x
        assert phone_specs.brand == expected_realme['brand']
        assert phone_specs.model == expected_realme['model']
        assert phone_specs.device_type == expected_realme['device_type']
        assert phone_specs.release_date == expected_realme['release_date']
        assert phone_specs.operating_system == expected_realme['operating_system']
        assert phone_specs.os_version == expected_realme['os_version']
        assert phone_specs.chipset == expected_realme['chipset']
        assert phone_specs.gpu == expected_realme['gpu']
    
    def test_data_consistency_across_formats(self, temp_output_dir):
        """Test data consistency between JSON and CSV exports."""
        # Create sample phone specifications
        phone_specs = [
            PhoneSpecifications(
                brand="Samsung",
                model="Galaxy S21",
                device_type="Smartphone",
                operating_system="Android",
                os_version="v11",
                chipset="Exynos 2100",
                cpu="Octa-core",
                gpu="Mali-G78 MP14",
                display_type="Dynamic AMOLED 2X",
                screen_size="6.2 inches",
                resolution="1080 x 2400 pixels",
                primary_camera_resolution="64MP",
                battery_capacity="4000mAh",
                ram="8GB",
                internal_storage="128GB"
            ),
            PhoneSpecifications(
                brand="Apple",
                model="iPhone 13",
                device_type="Smartphone",
                operating_system="iOS",
                os_version="v15",
                chipset="A15 Bionic",
                cpu="Hexa-core",
                display_type="Super Retina XDR OLED",
                screen_size="6.1 inches",
                resolution="1170 x 2532 pixels",
                primary_camera_resolution="12MP",
                battery_capacity="3240mAh",
                ram="6GB",
                internal_storage="128GB"
            )
        ]
        
        # Create scraper and export data
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        export_results = scraper._export_data(phone_specs)
        
        # Verify export success
        assert export_results['success'] is True
        assert export_results['record_count'] == 2
        
        # Load JSON data
        json_file = export_results['files']['json']
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Load CSV data
        csv_file = export_results['files']['csv']
        with open(csv_file, 'r', encoding='utf-8', newline='') as f:
            csv_reader = csv.DictReader(f)
            csv_data = list(csv_reader)
        
        # Verify data consistency
        assert len(json_data) == len(csv_data) == 2
        
        # Check each record for consistency
        for i, (json_record, csv_record) in enumerate(zip(json_data, csv_data)):
            # Key fields should match
            assert json_record['brand'] == csv_record['brand']
            assert json_record['model'] == csv_record['model']
            assert json_record['device_type'] == csv_record['device_type']
            assert json_record['operating_system'] == csv_record['operating_system']
            assert json_record['chipset'] == csv_record['chipset']
            
            # Verify against original data
            original_spec = phone_specs[i]
            assert json_record['brand'] == original_spec.brand
            assert json_record['model'] == original_spec.model
            assert json_record['chipset'] == original_spec.chipset
    
    def test_missing_data_handling(self, sample_fixtures):
        """Test handling of missing or incomplete data."""
        # Create mock HTTP client with incomplete data
        mock_client = Mock(spec=HTTPClient)
        
        # Create HTML with missing specification sections
        incomplete_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <section class="desc-box" id="product-specs">
                <div class="product-specs-tbl">
                    <div class="row mb-2 pb-2 border-bottom">
                        <div class="col-md-2">
                            <h3>General</h3>
                        </div>
                        <div class="col-md-10">
                            <table class="spec-grp-tbl">
                                <tbody>
                                    <tr>
                                        <td class="td1">Brand</td>
                                        <td class="td2">Unknown Brand</td>
                                    </tr>
                                    <!-- Missing Model, Device Type, etc. -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <!-- Missing other specification sections -->
                </div>
            </section>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = incomplete_html
        mock_response.content = incomplete_html.encode('utf-8')  # Add content attribute
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()  # Add this method
        mock_client.get.return_value = mock_response
        
        # Create detail scraper and extract data
        detail_scraper = DetailScraper(mock_client)
        phone_specs = detail_scraper.scrape_phone_details("http://test.com", "image.jpg")
        
        # Verify graceful handling of missing data
        assert phone_specs is not None
        assert phone_specs.brand == "Unknown Brand"
        assert phone_specs.model is None or phone_specs.model == ""
        assert phone_specs.device_type is None or phone_specs.device_type == ""
        
        # Verify data structure is still valid
        specs_dict = phone_specs.to_dict()
        assert isinstance(specs_dict, dict)
        assert 'brand' in specs_dict
        assert 'model' in specs_dict
        assert 'scraped_at' in specs_dict
    
    def test_data_type_validation(self):
        """Test data type validation and conversion."""
        # Test with various data types
        phone_specs = PhoneSpecifications(
            brand="Test Brand",
            model="Test Model",
            device_type="Smartphone",
            # Test numeric fields as strings (common in web scraping)
            battery_capacity="5000mAh",
            ram="8GB",
            internal_storage="256GB",
            screen_size="6.5 inches",
            # Test boolean-like fields
            waterproof="Yes",
            face_unlock="Supported"
        )
        
        # Validate data types
        assert isinstance(phone_specs.brand, str)
        assert isinstance(phone_specs.model, str)
        assert isinstance(phone_specs.battery_capacity, str)
        
        # Test dictionary conversion
        specs_dict = phone_specs.to_dict()
        assert isinstance(specs_dict['brand'], str)
        assert isinstance(specs_dict['battery_capacity'], str)
        
        # Test validation
        assert phone_specs.validate() is True
    
    def test_special_characters_handling(self):
        """Test handling of special characters and encoding."""
        # Test with special characters common in phone specifications
        phone_specs = PhoneSpecifications(
            brand="Xiaomi",
            model="Mi 11 Ultra",
            device_type="Smartphone",
            cpu="Octa-core (1×3.2 GHz Kryo 680 & 3×2.42 GHz Kryo 680 & 4×1.80 GHz Kryo 680)",
            display_type="AMOLED, 1B colors, 120Hz, HDR10+, 1700 nits (peak)",
            resolution="1440 × 3200 pixels, 20:9 ratio (~515 ppi density)",
            primary_camera_features="Leica optics, Dual-LED dual-tone flash, HDR, panorama",
            colors="Ceramic Black, Ceramic White"
        )
        
        # Test dictionary conversion with special characters
        specs_dict = phone_specs.to_dict()
        assert "×" in specs_dict['cpu']
        assert "±" not in specs_dict['cpu'] or "×" in specs_dict['cpu']  # Should preserve multiplication symbol
        assert ":" in specs_dict['resolution']
        
        # Test validation with special characters
        assert phone_specs.validate() is True
    
    @patch('mobiledokan_scraper.utils.http_client.HTTPClient.get')
    def test_end_to_end_data_accuracy(self, mock_get, sample_fixtures, temp_output_dir):
        """Test end-to-end data accuracy from scraping to export."""
        # Set up mock responses
        mock_response_listing = Mock()
        mock_response_listing.text = sample_fixtures['sample_listing_page']
        mock_response_listing.content = sample_fixtures['sample_listing_page'].encode('utf-8')
        mock_response_listing.status_code = 200
        mock_response_listing.raise_for_status = Mock()
        
        mock_response_detail = Mock()
        mock_response_detail.text = sample_fixtures['sample_detail_page']
        mock_response_detail.content = sample_fixtures['sample_detail_page'].encode('utf-8')
        mock_response_detail.status_code = 200
        mock_response_detail.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_response_listing, mock_response_detail]
        
        # Run complete workflow
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        results = scraper.run_complete_scraping(max_phones=1)
        
        # Verify workflow success
        assert results['success'] is True
        assert results['statistics']['successful_scrapes'] >= 1
        
        # Verify exported data accuracy
        json_file = results['export_results']['files']['json']
        with open(json_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        # Check first exported phone
        first_phone = exported_data[0]
        assert first_phone['brand'] == "Realme"
        assert first_phone['model'] == "Note 60x"
        assert first_phone['device_type'] == "Smartphone"
        assert "Android" in first_phone['operating_system']  # Allow for version info
        assert first_phone['chipset'] == "Unisoc Tiger T612"
        
        # Verify metadata
        assert 'scraped_at' in first_phone
        assert 'detail_url' in first_phone
        assert 'image_url' in first_phone
    
    def test_large_dataset_validation(self, temp_output_dir):
        """Test data validation with large datasets."""
        # Create a large dataset
        large_dataset = []
        for i in range(100):
            phone_specs = PhoneSpecifications(
                brand=f"Brand {i % 10}",  # 10 different brands
                model=f"Model {i}",
                device_type="Smartphone",
                operating_system="Android" if i % 2 == 0 else "iOS",
                os_version=f"v{10 + (i % 5)}",
                chipset=f"Chipset {i % 20}",
                ram=f"{4 + (i % 4) * 2}GB",
                internal_storage=f"{64 * (2 ** (i % 4))}GB",
                battery_capacity=f"{3000 + (i % 10) * 100}mAh"
            )
            large_dataset.append(phone_specs)
        
        # Export large dataset
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        export_results = scraper._export_data(large_dataset)
        
        # Verify export success
        assert export_results['success'] is True
        assert export_results['record_count'] == 100
        
        # Verify data integrity
        json_file = export_results['files']['json']
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        assert len(json_data) == 100
        
        # Verify data consistency
        for i, record in enumerate(json_data):
            assert record['brand'] == f"Brand {i % 10}"
            assert record['model'] == f"Model {i}"
            assert record['device_type'] == "Smartphone"
            assert record['ram'] == f"{4 + (i % 4) * 2}GB"