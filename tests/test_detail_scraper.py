"""
Unit tests for the DetailScraper class.

Tests the functionality of extracting phone specifications from detail pages,
including HTML parsing, field mapping, data normalization, and error handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from bs4 import BeautifulSoup

from mobiledokan_scraper.scrapers.detail_scraper import DetailScraper
from mobiledokan_scraper.utils.http_client import HTTPClient
from mobiledokan_scraper.models.phone_data import PhoneSpecifications


class TestDetailScraper(unittest.TestCase):
    """Test cases for DetailScraper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_http_client = Mock(spec=HTTPClient)
        self.scraper = DetailScraper(self.mock_http_client)
        
        # Load sample HTML fixture
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_detail_page.html')
        with open(fixture_path, 'r', encoding='utf-8') as f:
            self.sample_html = f.read()
    
    def test_init(self):
        """Test DetailScraper initialization."""
        self.assertIsInstance(self.scraper.http_client, HTTPClient)
        self.assertIsNotNone(self.scraper.logger)
    
    def test_scrape_phone_details_success(self):
        """Test successful phone details scraping."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.sample_html.encode('utf-8')
        self.mock_http_client.get.return_value = mock_response
        
        # Test scraping
        phone_url = "https://www.mobiledokan.com/mobile/realme-note-60x"
        image_url = "https://example.com/image.jpg"
        
        result = self.scraper.scrape_phone_details(phone_url, image_url)
        
        # Verify result
        self.assertIsInstance(result, PhoneSpecifications)
        self.assertEqual(result.brand, "Realme")
        self.assertEqual(result.model, "Note 60x")
        self.assertEqual(result.device_type, "Smartphone")
        self.assertEqual(result.detail_url, phone_url)
        self.assertEqual(result.image_url, image_url)
        self.assertIsNotNone(result.scraped_at)
        
        # Verify HTTP client was called
        self.mock_http_client.get.assert_called_once_with(phone_url)
    
    def test_scrape_phone_details_http_failure(self):
        """Test handling of HTTP request failure."""
        # Mock failed HTTP response
        mock_response = Mock()
        mock_response.status_code = 404
        self.mock_http_client.get.return_value = mock_response
        
        result = self.scraper.scrape_phone_details("https://example.com/invalid")
        
        self.assertIsNone(result)
    
    def test_scrape_phone_details_no_response(self):
        """Test handling when HTTP client returns None."""
        self.mock_http_client.get.return_value = None
        
        result = self.scraper.scrape_phone_details("https://example.com/invalid")
        
        self.assertIsNone(result)
    
    def test_scrape_phone_details_exception(self):
        """Test handling of exceptions during scraping."""
        # Mock HTTP client to raise exception
        self.mock_http_client.get.side_effect = Exception("Network error")
        
        result = self.scraper.scrape_phone_details("https://example.com/error")
        
        self.assertIsNone(result)
    
    def test_extract_specifications(self):
        """Test specification extraction from HTML."""
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        
        specifications = self.scraper.extract_specifications(soup)
        
        # Verify extracted specifications
        self.assertIsInstance(specifications, dict)
        self.assertGreater(len(specifications), 0)
        
        # Check specific fields
        self.assertEqual(specifications.get('brand'), 'Realme')
        self.assertEqual(specifications.get('model'), 'Note 60x')
        self.assertEqual(specifications.get('device_type'), 'Smartphone')
        self.assertEqual(specifications.get('operating_system'), 'Android')
        self.assertEqual(specifications.get('display_type'), 'IPS LCD')
        self.assertEqual(specifications.get('battery_capacity'), '5000 mAh')
    
    def test_extract_specifications_no_section(self):
        """Test specification extraction when no specs section exists."""
        html_without_specs = "<html><body><div>No specs here</div></body></html>"
        soup = BeautifulSoup(html_without_specs, 'html.parser')
        
        specifications = self.scraper.extract_specifications(soup)
        
        self.assertIsInstance(specifications, dict)
        self.assertEqual(len(specifications), 0)
    
    def test_parse_specification_category(self):
        """Test parsing of a single specification category."""
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        
        # Find the General category row
        general_row = soup.find('div', class_='row mb-2 pb-2 border-bottom')
        
        category_specs = self.scraper._parse_specification_category(general_row)
        
        # Verify parsed specifications
        self.assertIsInstance(category_specs, dict)
        self.assertGreater(len(category_specs), 0)
        self.assertEqual(category_specs.get('brand'), 'Realme')
        self.assertEqual(category_specs.get('model'), 'Note 60x')
        self.assertEqual(category_specs.get('device_type'), 'Smartphone')
    
    def test_parse_specification_category_no_table(self):
        """Test parsing category with no specification table."""
        html_no_table = '''
        <div class="row mb-2 pb-2 border-bottom">
            <div class="col-md-2">
                <h3 class="text-bold h6">Test Category</h3>
            </div>
            <div class="col-md-10">
                <p>No table here</p>
            </div>
        </div>
        '''
        soup = BeautifulSoup(html_no_table, 'html.parser')
        row = soup.find('div', class_='row')
        
        category_specs = self.scraper._parse_specification_category(row)
        
        self.assertIsInstance(category_specs, dict)
        self.assertEqual(len(category_specs), 0)
    
    def test_parse_specification_row(self):
        """Test parsing of a single specification row."""
        html_row = '''
        <tr>
            <td class="td1 ss">Brand</td>
            <td class="td2 ss">Realme</td>
        </tr>
        '''
        soup = BeautifulSoup(html_row, 'html.parser')
        row = soup.find('tr')
        
        spec_data = self.scraper._parse_specification_row(row)
        
        self.assertIsInstance(spec_data, dict)
        self.assertEqual(spec_data.get('brand'), 'Realme')
    
    def test_parse_specification_row_invalid(self):
        """Test parsing of invalid specification row."""
        html_row = '''
        <tr>
            <td class="td1 ss">Only one cell</td>
        </tr>
        '''
        soup = BeautifulSoup(html_row, 'html.parser')
        row = soup.find('tr')
        
        spec_data = self.scraper._parse_specification_row(row)
        
        self.assertIsNone(spec_data)
    
    def test_parse_specification_row_unknown_field(self):
        """Test parsing row with unknown field name."""
        html_row = '''
        <tr>
            <td class="td1 ss">Unknown Field</td>
            <td class="td2 ss">Some Value</td>
        </tr>
        '''
        soup = BeautifulSoup(html_row, 'html.parser')
        row = soup.find('tr')
        
        spec_data = self.scraper._parse_specification_row(row)
        
        self.assertIsNone(spec_data)
    
    def test_extract_cell_value_with_svg(self):
        """Test extracting cell value that contains SVG elements."""
        html_cell = '''
        <td class="td2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                <path d="test"/>
            </svg>
            Available
        </td>
        '''
        soup = BeautifulSoup(html_cell, 'html.parser')
        cell = soup.find('td')
        
        value = self.scraper._extract_cell_value(cell)
        
        self.assertEqual(value, 'Available')
    
    def test_extract_cell_value_complex(self):
        """Test extracting cell value with complex HTML structure."""
        html_cell = '''
        <td class="td2 ss">
            <span>6.74 inches</span>
            <small>(17.12 cm)</small>
        </td>
        '''
        soup = BeautifulSoup(html_cell, 'html.parser')
        cell = soup.find('td')
        
        value = self.scraper._extract_cell_value(cell)
        
        self.assertIn('6.74 inches', value)
        self.assertIn('17.12 cm', value)
    
    def test_extract_cell_value_empty(self):
        """Test extracting value from empty cell."""
        html_cell = '<td class="td2"></td>'
        soup = BeautifulSoup(html_cell, 'html.parser')
        cell = soup.find('td')
        
        value = self.scraper._extract_cell_value(cell)
        
        self.assertEqual(value, '')
    
    def test_normalize_specification_value_boolean(self):
        """Test normalization of boolean-like specification values."""
        # Test boolean field normalization
        result = self.scraper._normalize_specification_value('waterproof', 'Yes')
        self.assertEqual(result, 'Yes')
        
        result = self.scraper._normalize_specification_value('waterproof', 'No')
        self.assertEqual(result, 'No')
        
        result = self.scraper._normalize_specification_value('waterproof', 'Available')
        self.assertEqual(result, 'Yes')
    
    def test_normalize_specification_value_numeric(self):
        """Test normalization of numeric specification values."""
        # Test numeric field with unit
        result = self.scraper._normalize_specification_value('screen_size', '6.74 inches')
        self.assertIn('6.74', result)
        
        result = self.scraper._normalize_specification_value('battery_capacity', '5000 mAh')
        self.assertIn('5000', result)
        
        result = self.scraper._normalize_specification_value('weight', '200g')
        self.assertIn('200', result)
    
    def test_normalize_specification_value_text(self):
        """Test normalization of regular text specification values."""
        result = self.scraper._normalize_specification_value('brand', 'Realme')
        self.assertEqual(result, 'Realme')
        
        result = self.scraper._normalize_specification_value('chipset', 'Unisoc Tiger T612')
        self.assertEqual(result, 'Unisoc Tiger T612')
    
    def test_normalize_specification_value_empty(self):
        """Test normalization of empty specification values."""
        result = self.scraper._normalize_specification_value('brand', '')
        self.assertEqual(result, '')
        
        result = self.scraper._normalize_specification_value('brand', None)
        self.assertEqual(result, '')
    
    @patch('mobiledokan_scraper.scrapers.detail_scraper.datetime')
    def test_scrape_phone_details_metadata(self, mock_datetime):
        """Test that metadata is properly added to scraped phone details."""
        # Mock datetime
        mock_datetime.now.return_value.isoformat.return_value = '2025-01-01T12:00:00'
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.sample_html.encode('utf-8')
        self.mock_http_client.get.return_value = mock_response
        
        phone_url = "https://www.mobiledokan.com/mobile/test-phone"
        image_url = "https://example.com/test-image.jpg"
        
        result = self.scraper.scrape_phone_details(phone_url, image_url)
        
        # Verify metadata
        self.assertEqual(result.detail_url, phone_url)
        self.assertEqual(result.image_url, image_url)
        self.assertEqual(result.scraped_at, '2025-01-01T12:00:00')
    
    def test_comprehensive_specification_extraction(self):
        """Test comprehensive extraction of all specification categories."""
        soup = BeautifulSoup(self.sample_html, 'html.parser')
        
        specifications = self.scraper.extract_specifications(soup)
        
        # Verify all major categories are extracted
        expected_fields = [
            'brand', 'model', 'device_type', 'release_date', 'status',  # General
            'operating_system', 'os_version', 'chipset', 'cpu', 'gpu',  # Hardware
            'display_type', 'screen_size', 'resolution', 'pixel_density',  # Display
            'primary_camera_setup', 'primary_camera_resolution', 'selfie_camera_resolution',  # Cameras
            'battery_type', 'battery_capacity', 'quick_charging'  # Battery
        ]
        
        for field in expected_fields:
            self.assertIn(field, specifications, f"Missing field: {field}")
            self.assertIsNotNone(specifications[field], f"Field {field} is None")
            self.assertNotEqual(specifications[field], '', f"Field {field} is empty")


if __name__ == '__main__':
    unittest.main()