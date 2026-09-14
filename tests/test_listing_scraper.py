"""
Unit tests for the ListingScraper class.

Tests the functionality of extracting phone URLs from MobileDokan category pages,
including JSON data extraction, pagination handling, and filtering logic.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from mobiledokan_scraper.scrapers.listing_scraper import ListingScraper
from mobiledokan_scraper.utils.http_client import HTTPClient


class TestListingScraper(unittest.TestCase):
    """Test cases for ListingScraper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_http_client = Mock(spec=HTTPClient)
        self.scraper = ListingScraper(self.mock_http_client)
    
    def test_init(self):
        """Test ListingScraper initialization."""
        self.assertEqual(self.scraper.http_client, self.mock_http_client)
        self.assertIsNotNone(self.scraper.logger)
    
    def test_extract_phones_from_javascript_valid_data(self):
        """Test extraction of phone data from JavaScript with valid data."""
        # Sample HTML with embedded JavaScript data
        html_content = '''
        <html>
        <body>
        <script>
            let productDataArray = {
                "current_page": 1,
                "data": [
                    {
                        "id": 1,
                        "type": "mobile",
                        "title": "iPhone 15 Pro",
                        "slug": "iphone-15-pro",
                        "thamnail": "media/iphone-15-pro.webp",
                        "brand": "Apple",
                        "price_official": 120000,
                        "price_unofficial": null,
                        "ram": "8GB",
                        "storage": "256GB"
                    },
                    {
                        "id": 2,
                        "type": "mobile",
                        "title": "Samsung Galaxy S24",
                        "slug": "samsung-galaxy-s24",
                        "thamnail": "media/galaxy-s24.webp",
                        "brand": "Samsung",
                        "price_official": 85000,
                        "price_unofficial": null
                    }
                ]
            };
        </script>
        </body>
        </html>
        '''
        
        phones = self.scraper._extract_phones_from_javascript(html_content)
        
        self.assertEqual(len(phones), 2)
        
        # Check first phone
        phone1 = phones[0]
        self.assertEqual(phone1['title'], 'iPhone 15 Pro')
        self.assertEqual(phone1['slug'], 'iphone-15-pro')
        self.assertEqual(phone1['detail_url'], 'https://www.mobiledokan.com/mobile/iphone-15-pro')
        self.assertEqual(phone1['image_url'], 'https://www.mobiledokan.com/media/iphone-15-pro.webp')
        self.assertEqual(phone1['brand'], 'Apple')
        self.assertEqual(phone1['price_official'], 120000)
        
        # Check second phone
        phone2 = phones[1]
        self.assertEqual(phone2['title'], 'Samsung Galaxy S24')
        self.assertEqual(phone2['slug'], 'samsung-galaxy-s24')
        self.assertEqual(phone2['brand'], 'Samsung')
    
    def test_extract_phones_from_javascript_empty_data(self):
        """Test extraction with empty JavaScript data."""
        html_content = '''
        <html>
        <body>
        <script>
            let productDataArray = {"current_page": 1, "data": []};
        </script>
        </body>
        </html>
        '''
        
        phones = self.scraper._extract_phones_from_javascript(html_content)
        self.assertEqual(len(phones), 0)
    
    def test_extract_phones_from_javascript_no_data(self):
        """Test extraction with no JavaScript data."""
        html_content = '''
        <html>
        <body>
        <p>No JavaScript data here</p>
        </body>
        </html>
        '''
        
        phones = self.scraper._extract_phones_from_javascript(html_content)
        self.assertEqual(len(phones), 0)
    
    def test_extract_phones_from_javascript_invalid_json(self):
        """Test extraction with invalid JSON data."""
        html_content = '''
        <html>
        <body>
        <script>
            let productDataArray = {invalid json data};
        </script>
        </body>
        </html>
        '''
        
        phones = self.scraper._extract_phones_from_javascript(html_content)
        self.assertEqual(len(phones), 0)
    
    def test_is_valid_phone_data_valid(self):
        """Test validation of valid phone data."""
        valid_data = {
            'title': 'iPhone 15 Pro',
            'slug': 'iphone-15-pro',
            'type': 'mobile',
            'ram': '8GB'
        }
        
        self.assertTrue(self.scraper._is_valid_phone_data(valid_data))
    
    def test_is_valid_phone_data_missing_required_fields(self):
        """Test validation with missing required fields."""
        invalid_data = {
            'title': 'iPhone 15 Pro'
            # Missing 'slug'
        }
        
        self.assertFalse(self.scraper._is_valid_phone_data(invalid_data))
    
    def test_is_valid_phone_data_wrong_type(self):
        """Test validation with wrong device type."""
        invalid_data = {
            'title': 'Laptop Computer',
            'slug': 'laptop-computer',
            'type': 'laptop'
        }
        
        self.assertFalse(self.scraper._is_valid_phone_data(invalid_data))
    
    def test_is_valid_phone_data_no_phone_keywords(self):
        """Test validation with no phone-related keywords."""
        # Data without phone keywords and mobile fields should be invalid
        invalid_data = {
            'title': 'Random Product',
            'slug': 'random-product'
        }
        
        self.assertFalse(self.scraper._is_valid_phone_data(invalid_data))
        
        # But if it has mobile fields, it should be valid
        valid_data = {
            'title': 'Random Product',
            'slug': 'random-product',
            'ram': '8GB'
        }
        
        self.assertTrue(self.scraper._is_valid_phone_data(valid_data))
    
    def test_convert_phone_data_complete(self):
        """Test conversion of complete phone data."""
        raw_data = {
            'title': 'iPhone 15 Pro',
            'slug': 'iphone-15-pro',
            'thamnail': 'media/iphone-15-pro.webp',
            'brand': 'Apple',
            'price_official': 120000,
            'price_unofficial': None,
            'release_date': '2023-09-15',
            'avibility': 'In Stock',
            'ram': '8GB',
            'storage': '256GB',
            'display': '6.1"',
            'main_camera': '48MP',
            'battery': '3274mAh',
            'os': 'iOS 17'
        }
        
        converted = self.scraper._convert_phone_data(raw_data)
        
        self.assertIsNotNone(converted)
        self.assertEqual(converted['title'], 'iPhone 15 Pro')
        self.assertEqual(converted['slug'], 'iphone-15-pro')
        self.assertEqual(converted['detail_url'], 'https://www.mobiledokan.com/mobile/iphone-15-pro')
        self.assertEqual(converted['image_url'], 'https://www.mobiledokan.com/media/iphone-15-pro.webp')
        self.assertEqual(converted['brand'], 'Apple')
        self.assertEqual(converted['price_official'], 120000)
        self.assertEqual(converted['ram'], '8GB')
    
    def test_convert_phone_data_missing_slug(self):
        """Test conversion with missing slug."""
        raw_data = {
            'title': 'iPhone 15 Pro'
            # Missing slug
        }
        
        converted = self.scraper._convert_phone_data(raw_data)
        self.assertIsNone(converted)
    
    def test_extract_brand_from_title_known_brands(self):
        """Test brand extraction from titles with known brands."""
        test_cases = [
            ('iPhone 15 Pro', 'Apple'),
            ('Samsung Galaxy S24', 'Samsung'),
            ('Google Pixel 8', 'Google'),
            ('OnePlus 12', 'OnePlus'),
            ('Xiaomi Mi 14', 'Xiaomi'),
            ('Realme GT 5', 'Realme'),
            ('OPPO Find X7', 'Oppo'),
            ('Vivo V30 Pro', 'Vivo'),
            ('Nothing Phone 2', 'Nothing'),
            ('Infinix Smart 8', 'Infinix')
        ]
        
        for title, expected_brand in test_cases:
            with self.subTest(title=title):
                brand = self.scraper._extract_brand_from_title(title)
                self.assertEqual(brand, expected_brand)
    
    def test_extract_brand_from_title_unknown_brand(self):
        """Test brand extraction from titles with unknown brands."""
        # Should return first word as brand
        brand = self.scraper._extract_brand_from_title('NewBrand Phone X1')
        self.assertEqual(brand, 'Newbrand')
        
        # Should return 'Unknown' for very short or empty titles
        self.assertEqual(self.scraper._extract_brand_from_title(''), 'Unknown')
        self.assertEqual(self.scraper._extract_brand_from_title('AB'), 'Unknown')
    
    def test_filter_valid_phones_removes_duplicates(self):
        """Test that filtering removes duplicate phones."""
        phones = [
            {
                'title': 'iPhone 15 Pro',
                'slug': 'iphone-15-pro',
                'detail_url': 'https://www.mobiledokan.com/mobile/iphone-15-pro'
            },
            {
                'title': 'iPhone 15 Pro',
                'slug': 'iphone-15-pro',  # Duplicate slug
                'detail_url': 'https://www.mobiledokan.com/mobile/iphone-15-pro'
            },
            {
                'title': 'Samsung Galaxy S24',
                'slug': 'samsung-galaxy-s24',
                'detail_url': 'https://www.mobiledokan.com/mobile/samsung-galaxy-s24'
            }
        ]
        
        filtered = self.scraper._filter_valid_phones(phones)
        self.assertEqual(len(filtered), 2)  # Should remove one duplicate
        
        # Check that we kept the unique ones
        slugs = [phone['slug'] for phone in filtered]
        self.assertIn('iphone-15-pro', slugs)
        self.assertIn('samsung-galaxy-s24', slugs)
    
    def test_filter_valid_phones_removes_ads(self):
        """Test that filtering removes advertisement content."""
        phones = [
            {
                'title': 'iPhone 15 Pro',
                'slug': 'iphone-15-pro',
                'detail_url': 'https://www.mobiledokan.com/mobile/iphone-15-pro'
            },
            {
                'title': 'Special Advertisement Offer',
                'slug': 'special-advertisement-offer',
                'detail_url': 'https://www.mobiledokan.com/mobile/special-advertisement-offer'
            },
            {
                'title': 'Sponsored Content Deal',
                'slug': 'sponsored-content-deal',
                'detail_url': 'https://www.mobiledokan.com/mobile/sponsored-content-deal'
            }
        ]
        
        filtered = self.scraper._filter_valid_phones(phones)
        self.assertEqual(len(filtered), 1)  # Should keep only the iPhone
        self.assertEqual(filtered[0]['title'], 'iPhone 15 Pro')
    
    def test_filter_valid_phones_removes_invalid_urls(self):
        """Test that filtering removes phones with invalid URLs."""
        phones = [
            {
                'title': 'iPhone 15 Pro',
                'slug': 'iphone-15-pro',
                'detail_url': 'https://www.mobiledokan.com/mobile/iphone-15-pro'
            },
            {
                'title': 'Samsung Galaxy S24',
                'slug': 'samsung-galaxy-s24',
                'detail_url': 'https://www.mobiledokan.com/category/accessories'  # Invalid URL
            },
            {
                'title': 'Google Pixel 8',
                'slug': 'google-pixel-8',
                'detail_url': ''  # Empty URL
            }
        ]
        
        filtered = self.scraper._filter_valid_phones(phones)
        self.assertEqual(len(filtered), 1)  # Should keep only the iPhone
        self.assertEqual(filtered[0]['title'], 'iPhone 15 Pro')
    
    def test_get_next_page_from_javascript_with_pagination(self):
        """Test next page detection from JavaScript with pagination data."""
        html_content = '''
        <script>
            let productDataArray = {
                "current_page": 1,
                "last_page": 5,
                "data": [{"title": "Phone 1", "slug": "phone-1"}]
            };
        </script>
        '''
        
        next_url = self.scraper._get_next_page_from_javascript(html_content, 1)
        self.assertEqual(next_url, 'https://www.mobiledokan.com/mobile-category/smartphone?page=2')
    
    def test_get_next_page_from_javascript_last_page(self):
        """Test next page detection when on last page."""
        html_content = '''
        <script>
            let productDataArray = {
                "current_page": 5,
                "last_page": 5,
                "data": [{"title": "Phone 1", "slug": "phone-1"}]
            };
        </script>
        '''
        
        next_url = self.scraper._get_next_page_from_javascript(html_content, 5)
        self.assertIsNone(next_url)
    
    def test_get_next_page_from_javascript_no_data(self):
        """Test next page detection with no data on page."""
        html_content = '''
        <script>
            let productDataArray = {
                "current_page": 10,
                "data": []
            };
        </script>
        '''
        
        next_url = self.scraper._get_next_page_from_javascript(html_content, 10)
        self.assertIsNone(next_url)
    
    def test_page_has_phone_content_with_javascript(self):
        """Test phone content detection with JavaScript data."""
        html_content = '''
        <script>
            let productDataArray = {"data": [{"title": "Phone"}]};
        </script>
        '''
        
        has_content = self.scraper._page_has_phone_content(html_content)
        self.assertTrue(has_content)
    
    def test_page_has_phone_content_with_html(self):
        """Test phone content detection with HTML elements."""
        html_content = '''
        <html>
        <body>
            <a href="/mobile/iphone-15">iPhone 15</a>
        </body>
        </html>
        '''
        
        has_content = self.scraper._page_has_phone_content(html_content)
        self.assertTrue(has_content)
    
    def test_page_has_phone_content_no_content(self):
        """Test phone content detection with no phone content."""
        html_content = '''
        <html>
        <body>
            <p>No phones here</p>
        </body>
        </html>
        '''
        
        has_content = self.scraper._page_has_phone_content(html_content)
        self.assertFalse(has_content)
    
    @patch('mobiledokan_scraper.scrapers.listing_scraper.BeautifulSoup')
    def test_extract_phones_from_html_fallback(self, mock_soup):
        """Test HTML parsing fallback when JavaScript extraction fails."""
        # Mock BeautifulSoup to return phone links
        mock_soup_instance = Mock()
        mock_soup.return_value = mock_soup_instance
        
        # Mock phone link element
        mock_link = Mock()
        mock_link.get.side_effect = lambda attr, default='': {
            'href': '/mobile/test-phone',
            'title': 'Test Phone'
        }.get(attr, default)
        mock_link.get_text.return_value = 'Test Phone'
        mock_link.find.return_value = None  # No image
        
        mock_soup_instance.select.return_value = [mock_link]
        
        html_content = '<html><body><a href="/mobile/test-phone">Test Phone</a></body></html>'
        
        phones = self.scraper._extract_phones_from_html(html_content)
        
        self.assertEqual(len(phones), 1)
        self.assertEqual(phones[0]['title'], 'Test Phone')
        self.assertEqual(phones[0]['slug'], 'test-phone')
        self.assertEqual(phones[0]['detail_url'], 'https://www.mobiledokan.com/mobile/test-phone')
    
    def test_extract_phone_urls_from_page_integration(self):
        """Test the main extraction method with sample HTML."""
        html_content = '''
        <html>
        <body>
        <script>
            let productDataArray = {
                "current_page": 1,
                "data": [
                    {
                        "id": 1,
                        "type": "mobile",
                        "title": "iPhone 15 Pro",
                        "slug": "iphone-15-pro",
                        "thamnail": "media/iphone-15-pro.webp",
                        "brand": "Apple",
                        "price_official": 120000
                    }
                ]
            };
        </script>
        </body>
        </html>
        '''
        
        phones = self.scraper.extract_phone_urls_from_page(html_content)
        
        self.assertEqual(len(phones), 1)
        self.assertEqual(phones[0]['title'], 'iPhone 15 Pro')
        self.assertEqual(phones[0]['brand'], 'Apple')


class TestListingScraperWithFixtures(unittest.TestCase):
    """Integration tests using HTML fixtures."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_http_client = Mock(spec=HTTPClient)
        self.scraper = ListingScraper(self.mock_http_client)
    
    def _load_fixture(self, filename: str) -> str:
        """Load HTML fixture file."""
        import os
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', filename)
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def test_extract_phones_from_sample_listing_page(self):
        """Test extraction from sample listing page fixture."""
        html_content = self._load_fixture('sample_listing_page.html')
        
        phones = self.scraper.extract_phone_urls_from_page(html_content)
        
        # Should extract 2 valid phones (filtering out the advertisement)
        self.assertEqual(len(phones), 2)
        
        # Check first phone (Infinix Smart 8 Pro)
        infinix_phone = next((p for p in phones if p['slug'] == 'infinix-smart-8-pro'), None)
        self.assertIsNotNone(infinix_phone)
        self.assertEqual(infinix_phone['title'], 'Infinix Smart 8 Pro')
        self.assertEqual(infinix_phone['detail_url'], 'https://www.mobiledokan.com/mobile/infinix-smart-8-pro')
        self.assertEqual(infinix_phone['image_url'], 'https://www.mobiledokan.com/media/infinix-smart-8-pro-timber-black-official-image.webp')
        self.assertEqual(infinix_phone['price_official'], 11499)
        self.assertEqual(infinix_phone['ram'], '4GB')
        self.assertEqual(infinix_phone['storage'], '128GB')
        
        # Check second phone (Google Pixel 7)
        pixel_phone = next((p for p in phones if p['slug'] == 'google-pixel-7'), None)
        self.assertIsNotNone(pixel_phone)
        self.assertEqual(pixel_phone['title'], 'Google Pixel 7')
        self.assertEqual(pixel_phone['price_unofficial'], 43500)
        self.assertEqual(pixel_phone['ram'], '8GB')
    
    def test_extract_phones_from_empty_page(self):
        """Test extraction from empty page fixture."""
        html_content = self._load_fixture('sample_empty_page.html')
        
        phones = self.scraper.extract_phone_urls_from_page(html_content)
        
        # Should return empty list
        self.assertEqual(len(phones), 0)
    
    def test_get_next_page_url_from_sample_page(self):
        """Test next page URL detection from sample page."""
        html_content = self._load_fixture('sample_listing_page.html')
        
        next_url = self.scraper.get_next_page_url(html_content, 1)
        
        # Should detect next page from JavaScript data
        self.assertEqual(next_url, 'https://www.mobiledokan.com/mobile-category/smartphone?page=2')
    
    def test_get_next_page_url_from_empty_page(self):
        """Test next page URL detection from empty page."""
        html_content = self._load_fixture('sample_empty_page.html')
        
        next_url = self.scraper.get_next_page_url(html_content, 999)
        
        # Should return None since we're on page 999 and data is empty
        self.assertIsNone(next_url)
    
    @patch.object(ListingScraper, 'extract_phone_urls_from_page')
    @patch.object(ListingScraper, 'get_next_page_url')
    def test_scrape_all_phone_urls_multiple_pages(self, mock_get_next_page, mock_extract_phones):
        """Test scraping multiple pages."""
        # Mock HTTP responses
        mock_response1 = Mock()
        mock_response1.text = self._load_fixture('sample_listing_page.html')
        
        mock_response2 = Mock()
        mock_response2.text = self._load_fixture('sample_empty_page.html')
        
        self.mock_http_client.get.side_effect = [mock_response1, mock_response2]
        
        # Mock phone extraction
        mock_extract_phones.side_effect = [
            [{'title': 'Phone 1', 'slug': 'phone-1'}],  # Page 1
            []  # Page 2 (empty)
        ]
        
        # Mock next page detection
        mock_get_next_page.side_effect = [
            'https://www.mobiledokan.com/mobile-category/smartphone?page=2',  # From page 1
            None  # From page 2
        ]
        
        phones = self.scraper.scrape_all_phone_urls()
        
        # Should have made 2 HTTP requests
        self.assertEqual(self.mock_http_client.get.call_count, 2)
        
        # Should have extracted phones from first page only
        self.assertEqual(len(phones), 1)
        self.assertEqual(phones[0]['title'], 'Phone 1')
    
    @patch.object(ListingScraper, 'get_next_page_url')
    @patch.object(ListingScraper, 'extract_phone_urls_from_page')
    def test_scrape_all_phone_urls_single_page(self, mock_extract_phones, mock_get_next_page):
        """Test scraping single page with no pagination."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = self._load_fixture('sample_listing_page.html')
        self.mock_http_client.get.return_value = mock_response
        
        # Mock phone extraction
        mock_extract_phones.return_value = [
            {'title': 'Phone 1', 'slug': 'phone-1'},
            {'title': 'Phone 2', 'slug': 'phone-2'}
        ]
        
        # Mock no next page (single page scenario)
        mock_get_next_page.return_value = None
        
        phones = self.scraper.scrape_all_phone_urls()
        
        # Should have made 1 HTTP request
        self.assertEqual(self.mock_http_client.get.call_count, 1)
        
        # Should have extracted both phones
        self.assertEqual(len(phones), 2)
    
    def test_scrape_all_phone_urls_http_error(self):
        """Test handling of HTTP errors during scraping."""
        # Mock HTTP client to raise an exception
        self.mock_http_client.get.side_effect = Exception("Network error")
        
        phones = self.scraper.scrape_all_phone_urls()
        
        # Should return empty list on error
        self.assertEqual(len(phones), 0)


if __name__ == '__main__':
    unittest.main()