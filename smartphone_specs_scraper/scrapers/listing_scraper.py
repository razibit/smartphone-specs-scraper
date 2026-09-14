"""
Listing scraper for extracting smartphone URLs from MobileDokan category pages.

This module handles the extraction of phone URLs from paginated category pages,
including JSON data extraction from embedded JavaScript variables and pagination navigation.
"""

import re
import json
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

from ..utils.http_client import HTTPClient
from ..utils.error_handling import ParsingError, NetworkError, handle_parsing_error, log_and_continue
from ..config.settings import BASE_URL, DOMAIN


class ListingScraper:
    """
    Scraper for extracting smartphone URLs from MobileDokan category pages.
    
    This scraper handles:
    - Extraction of phone URLs from embedded JSON data
    - Pagination detection and navigation
    - Filtering out ads and non-mobile links
    - Image URL extraction for each phone
    """
    
    def __init__(self, http_client: HTTPClient):
        """
        Initialize the listing scraper.
        
        Args:
            http_client: HTTP client instance for making requests
        """
        self.http_client = http_client
        self.logger = logging.getLogger(__name__)
        
    def scrape_all_phone_urls(self, base_url: str = BASE_URL) -> List[Dict[str, str]]:
        """
        Scrape all smartphone URLs from all pages of the category.
        
        Args:
            base_url: Base URL of the smartphone category page
            
        Returns:
            List of dictionaries containing phone URLs and metadata
            
        Example return format:
            [
                {
                    'title': 'iPhone 15 Pro',
                    'slug': 'iphone-15-pro',
                    'detail_url': 'https://www.mobiledokan.com/mobile/iphone-15-pro',
                    'image_url': 'https://www.mobiledokan.com/media/iphone-15-pro.webp',
                    'brand': 'Apple',
                    'price_official': 120000,
                    'price_unofficial': None
                },
                ...
            ]
        """
        all_phones = []
        current_page = 1
        
        self.logger.info(f"Starting to scrape phone URLs from {base_url}")
        
        while True:
            # Construct URL for current page
            if current_page == 1:
                page_url = base_url
            else:
                page_url = f"{base_url}?page={current_page}"
            
            self.logger.info(f"Scraping page {current_page}: {page_url}")
            
            try:
                # Get the page content
                response = self.http_client.get(page_url)
                html_content = response.text
                
                # Extract phone URLs from this page
                page_phones = self.extract_phone_urls_from_page(html_content)
                
                if not page_phones:
                    self.logger.info(f"No phones found on page {current_page}, stopping pagination")
                    break
                
                all_phones.extend(page_phones)
                self.logger.info(f"Found {len(page_phones)} phones on page {current_page}")
                
                # Check if there's a next page
                next_page_url = self.get_next_page_url(html_content, current_page)
                if not next_page_url:
                    self.logger.info(f"No next page found after page {current_page}, stopping pagination")
                    break
                
                # Additional safety check: if we've been scraping for too many pages, stop
                if current_page >= 250:  # Safety limit to prevent infinite loops
                    self.logger.warning(f"Reached safety limit of 250 pages, stopping pagination")
                    break
                
                current_page += 1
                
            except Exception as e:
                self.logger.error(f"Error scraping page {current_page}: {e}")
                break
        
        self.logger.info(f"Completed scraping. Found {len(all_phones)} total phones across {current_page} pages")
        return all_phones
    
    def extract_phone_urls_from_page(self, html: str) -> List[Dict[str, str]]:
        """
        Extract phone URLs and metadata from a single page's HTML.
        
        This method looks for embedded JSON data in JavaScript variables,
        specifically the 'productDataArray' variable that contains phone information.
        
        Args:
            html: HTML content of the page
            
        Returns:
            List of dictionaries containing phone information
        """
        phones = []
        
        try:
            # First, try to extract JSON data from JavaScript variables
            phones_from_js = self._extract_phones_from_javascript(html)
            if phones_from_js:
                phones.extend(phones_from_js)
                self.logger.debug(f"Extracted {len(phones_from_js)} phones from JavaScript data")
            
            # If no JavaScript data found, fall back to HTML parsing
            if not phones:
                phones_from_html = self._extract_phones_from_html(html)
                phones.extend(phones_from_html)
                self.logger.debug(f"Extracted {len(phones_from_html)} phones from HTML parsing")
            
            # Filter out ads and non-mobile links
            filtered_phones = self._filter_valid_phones(phones)
            
            self.logger.debug(f"Filtered {len(phones)} phones to {len(filtered_phones)} valid phones")
            return filtered_phones
            
        except Exception as e:
            self.logger.error(f"Error extracting phone URLs from page: {e}")
            return []
    
    def _extract_phones_from_javascript(self, html: str) -> List[Dict[str, str]]:
        """
        Extract phone data from embedded JavaScript variables.
        
        Looks for patterns like:
        - let productDataArray = {...}
        - var phones = [...]
        
        Args:
            html: HTML content containing JavaScript
            
        Returns:
            List of phone dictionaries extracted from JavaScript
        """
        phones = []
        
        # Pattern to match productDataArray variable
        js_patterns = [
            r'let\s+productDataArray\s*=\s*(\{.*?\});',
            r'var\s+productDataArray\s*=\s*(\{.*?\});',
            r'productDataArray\s*=\s*(\{.*?\});',
            r'let\s+phones\s*=\s*(\[.*?\]);',
            r'var\s+phones\s*=\s*(\[.*?\]);'
        ]
        
        for pattern in js_patterns:
            matches = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if matches:
                try:
                    json_str = matches.group(1)
                    data = json.loads(json_str)
                    
                    # Handle different data structures
                    if isinstance(data, dict) and 'data' in data:
                        # Structure: {current_page: X, data: [...]}
                        phone_list = data['data']
                    elif isinstance(data, list):
                        # Structure: [...]
                        phone_list = data
                    else:
                        continue
                    
                    # Convert each phone item to our format
                    for phone_data in phone_list:
                        if isinstance(phone_data, dict) and self._is_valid_phone_data(phone_data):
                            phone_info = self._convert_phone_data(phone_data)
                            if phone_info:
                                phones.append(phone_info)
                    
                    if phones:
                        self.logger.debug(f"Successfully extracted {len(phones)} phones from JavaScript pattern: {pattern}")
                        break
                        
                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.debug(f"Failed to parse JSON from pattern {pattern}: {e}")
                    continue
        
        return phones
    
    def _extract_phones_from_html(self, html: str) -> List[Dict[str, str]]:
        """
        Extract phone data from HTML elements as fallback.
        
        Args:
            html: HTML content to parse
            
        Returns:
            List of phone dictionaries extracted from HTML
        """
        phones = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for phone links in various possible selectors
            phone_selectors = [
                'a[href*="/mobile/"]',
                '.phone-item a',
                '.product-item a',
                '.mobile-item a'
            ]
            
            for selector in phone_selectors:
                links = soup.select(selector)
                if links:
                    for link in links:
                        phone_info = self._extract_phone_from_link(link)
                        if phone_info:
                            phones.append(phone_info)
                    break  # Use the first selector that finds results
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML for phone links: {e}")
        
        return phones
    
    def _extract_phone_from_link(self, link_element) -> Optional[Dict[str, str]]:
        """
        Extract phone information from an HTML link element.
        
        Args:
            link_element: BeautifulSoup element representing a phone link
            
        Returns:
            Dictionary with phone information or None if invalid
        """
        try:
            href = link_element.get('href', '')
            if not href or '/mobile/' not in href:
                return None
            
            # Extract slug from URL
            slug = href.split('/mobile/')[-1].strip('/')
            if not slug:
                return None
            
            # Get title from link text or title attribute
            title = (
                link_element.get('title', '') or
                link_element.get_text(strip=True) or
                slug.replace('-', ' ').title()
            )
            
            # Look for image in the link
            img = link_element.find('img')
            image_url = ''
            if img:
                image_url = img.get('src', '') or img.get('data-src', '')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(DOMAIN, image_url)
            
            return {
                'title': title,
                'slug': slug,
                'detail_url': urljoin(DOMAIN, href),
                'image_url': image_url,
                'brand': self._extract_brand_from_title(title),
                'price_official': None,
                'price_unofficial': None
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting phone from link element: {e}")
            return None
    
    def _is_valid_phone_data(self, data: Dict[str, Any]) -> bool:
        """
        Check if the extracted data represents a valid phone entry.
        
        Args:
            data: Dictionary containing phone data
            
        Returns:
            True if the data represents a valid phone, False otherwise
        """
        # Check required fields
        required_fields = ['title', 'slug']
        if not all(field in data for field in required_fields):
            return False
        
        # Check if it's a mobile device
        if data.get('type') and data['type'] != 'mobile':
            return False
        
        # Check if title contains phone-like keywords
        title = data.get('title', '').lower()
        phone_keywords = ['phone', 'mobile', 'smartphone', 'iphone', 'galaxy', 'pixel', 'oneplus', 'xiaomi', 'realme', 'oppo', 'vivo', 'huawei', 'honor', 'nokia', 'samsung', 'lg', 'sony', 'motorola', 'asus', 'infinix', 'tecno']
        
        # If title doesn't contain any phone keywords, it might be an ad or other content
        if not any(keyword in title for keyword in phone_keywords):
            # Additional check: if it has mobile-specific fields, it's probably valid
            mobile_fields = ['ram', 'storage', 'battery', 'camera', 'display']
            if not any(field in data for field in mobile_fields):
                return False
        
        return True
    
    def _convert_phone_data(self, data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Convert raw phone data from JavaScript to our standardized format.
        
        Args:
            data: Raw phone data dictionary
            
        Returns:
            Standardized phone information dictionary
        """
        try:
            slug = data.get('slug', '')
            if not slug:
                return None
            
            # Build detail URL
            detail_url = f"{DOMAIN}/mobile/{slug}"
            
            # Handle image URL
            image_url = ''
            thumbnail = data.get('thamnail', '') or data.get('thumbnail', '')
            if thumbnail:
                if thumbnail.startswith('media/'):
                    image_url = f"{DOMAIN}/{thumbnail}"
                elif not thumbnail.startswith('http'):
                    image_url = urljoin(DOMAIN, thumbnail)
                else:
                    image_url = thumbnail
            
            # Extract brand from title or brand field
            title = data.get('title', '')
            brand_field = data.get('brand', '')
            
            # If brand is a number (ID), extract from title instead
            if isinstance(brand_field, (int, str)) and str(brand_field).isdigit():
                brand = self._extract_brand_from_title(title)
            else:
                brand = brand_field or self._extract_brand_from_title(title)
            
            # Handle prices
            price_official = data.get('price_official')
            price_unofficial = data.get('price_unofficial')
            
            # Convert to integers if they're numeric strings
            if isinstance(price_official, str) and price_official.isdigit():
                price_official = int(price_official)
            if isinstance(price_unofficial, str) and price_unofficial.isdigit():
                price_unofficial = int(price_unofficial)
            
            return {
                'title': title,
                'slug': slug,
                'detail_url': detail_url,
                'image_url': image_url,
                'brand': brand,
                'price_official': price_official,
                'price_unofficial': price_unofficial,
                'release_date': data.get('release_date', ''),
                'availability': data.get('avibility', ''),  # Note: typo in original data
                'ram': data.get('ram', ''),
                'storage': data.get('storage', ''),
                'display': data.get('display', ''),
                'main_camera': data.get('main_camera', ''),
                'battery': data.get('battery', ''),
                'os': data.get('os', '')
            }
            
        except Exception as e:
            self.logger.debug(f"Error converting phone data: {e}")
            return None
    
    def _extract_brand_from_title(self, title: str) -> str:
        """
        Extract brand name from phone title.
        
        Args:
            title: Phone title string
            
        Returns:
            Brand name or 'Unknown' if not found
        """
        if not title:
            return 'Unknown'
        
        # Common brand names (case-insensitive)
        brands = [
            'Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi', 'Realme', 'Oppo', 'Vivo',
            'Huawei', 'Honor', 'Nokia', 'LG', 'Sony', 'Motorola', 'Asus', 'Infinix',
            'Tecno', 'Nothing', 'Fairphone', 'Blackberry', 'HTC', 'Meizu', 'ZTE',
            'Alcatel', 'Lenovo', 'TCL', 'Poco', 'Redmi', 'Mi', 'iPhone'
        ]
        
        title_lower = title.lower()
        for brand in brands:
            if brand.lower() in title_lower:
                # Special case for iPhone -> Apple
                if brand.lower() == 'iphone':
                    return 'Apple'
                return brand
        
        # Try to extract first word as brand
        first_word = title.split()[0] if title.split() else ''
        if first_word and len(first_word) > 2:
            return first_word.title()
        
        return 'Unknown'
    
    def _filter_valid_phones(self, phones: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Filter out ads, duplicates, and non-mobile links from the phone list.
        
        Args:
            phones: List of phone dictionaries
            
        Returns:
            Filtered list of valid phone dictionaries
        """
        if not phones:
            return []
        
        valid_phones = []
        seen_slugs = set()
        
        for phone in phones:
            # Skip if missing required fields
            if not phone.get('slug') or not phone.get('title'):
                continue
            
            # Skip duplicates
            slug = phone['slug']
            if slug in seen_slugs:
                continue
            
            # Skip obvious ads or non-phone content
            title_lower = phone.get('title', '').lower()
            
            # Skip if title contains ad-related keywords
            ad_keywords = ['advertisement', 'sponsored', 'promo', 'offer', 'deal', 'discount']
            if any(keyword in title_lower for keyword in ad_keywords):
                continue
            
            # Skip if URL doesn't look like a phone URL
            detail_url = phone.get('detail_url', '')
            if not detail_url or '/mobile/' not in detail_url:
                continue
            
            # Skip if title is too short or generic
            if len(phone.get('title', '')) < 3:
                continue
            
            # Add to valid phones
            seen_slugs.add(slug)
            valid_phones.append(phone)
        
        return valid_phones
    
    def get_next_page_url(self, html: str, current_page: int) -> Optional[str]:
        """
        Detect if there's a next page and return its URL.
        
        Args:
            html: HTML content of the current page
            current_page: Current page number
            
        Returns:
            URL of the next page or None if no next page exists
        """
        try:
            # First, check if there's pagination data in JavaScript
            next_page_from_js = self._get_next_page_from_javascript(html, current_page)
            if next_page_from_js:
                return next_page_from_js
            
            # Fall back to HTML parsing
            return self._get_next_page_from_html(html, current_page)
            
        except Exception as e:
            self.logger.debug(f"Error detecting next page: {e}")
            return None
    
    def _get_next_page_from_javascript(self, html: str, current_page: int) -> Optional[str]:
        """
        Extract next page information from JavaScript data.
        
        Args:
            html: HTML content
            current_page: Current page number
            
        Returns:
            Next page URL or None
        """
        # Look for pagination data in JavaScript
        js_patterns = [
            r'let\s+productDataArray\s*=\s*(\{.*?\});',
            r'var\s+productDataArray\s*=\s*(\{.*?\});',
            r'productDataArray\s*=\s*(\{.*?\});'
        ]
        
        for pattern in js_patterns:
            matches = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if matches:
                try:
                    json_str = matches.group(1)
                    data = json.loads(json_str)
                    
                    if isinstance(data, dict):
                        current_page_in_data = data.get('current_page')
                        total_pages = data.get('last_page') or data.get('total_pages')
                        page_data = data.get('data', [])
                        
                        # If we have pagination info, check if we're at or past the last page
                        if current_page_in_data and total_pages:
                            if current_page_in_data >= total_pages:
                                return None
                            
                            # If there's no data on this page, we've reached the end
                            if not page_data:
                                return None
                            
                            # If we have data and we're not at the last page, return next page
                            if current_page_in_data < total_pages:
                                next_page = current_page + 1
                                return f"{BASE_URL}?page={next_page}"
                        
                        # If no pagination info but no data, assume no more pages
                        if not page_data:
                            return None
                            
                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.debug(f"Failed to parse pagination from JavaScript: {e}")
                    continue
        
        return None
    
    def _get_next_page_from_html(self, html: str, current_page: int) -> Optional[str]:
        """
        Extract next page URL from HTML pagination elements.
        
        Args:
            html: HTML content
            current_page: Current page number
            
        Returns:
            Next page URL or None
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for pagination links
            pagination_selectors = [
                'a[href*="?page="]',
                '.pagination a[href*="page"]',
                '.page-link[href*="page"]',
                'a[href*="page="]'
            ]
            
            for selector in pagination_selectors:
                links = soup.select(selector)
                if links:
                    # Look for next page link
                    next_page = current_page + 1
                    for link in links:
                        href = link.get('href', '')
                        if f'page={next_page}' in href:
                            if href.startswith('/'):
                                return urljoin(DOMAIN, href)
                            elif href.startswith('?'):
                                return f"{BASE_URL}{href}"
                            else:
                                return href
            
            # If no specific next page link found, be more conservative
            # Only continue if we have strong evidence of more content
            if self._page_has_phone_content(html) and current_page < 210:  # Conservative limit
                next_page = current_page + 1
                return f"{BASE_URL}?page={next_page}"
            
        except Exception as e:
            self.logger.debug(f"Error parsing HTML for next page: {e}")
        
        return None
    
    def _page_has_phone_content(self, html: str) -> bool:
        """
        Check if the page contains phone content.
        
        Args:
            html: HTML content to check
            
        Returns:
            True if page has phone content, False otherwise
        """
        # Check for JavaScript data with actual content
        js_patterns = [
            r'let\s+productDataArray\s*=\s*(\{.*?\});',
            r'var\s+productDataArray\s*=\s*(\{.*?\});',
            r'productDataArray\s*=\s*(\{.*?\});'
        ]
        
        for pattern in js_patterns:
            matches = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if matches:
                try:
                    json_str = matches.group(1)
                    data = json.loads(json_str)
                    
                    if isinstance(data, dict):
                        page_data = data.get('data', [])
                        # Check if we have actual phone data, not just empty objects
                        if page_data and len(page_data) > 0:
                            # A non-empty product payload is enough to confirm
                            # that the page contains content. Full validation
                            # remains the responsibility of the extractor.
                            return True
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Check for phone-related HTML content
        soup = BeautifulSoup(html, 'html.parser')
        phone_indicators = [
            'a[href*="/mobile/"]',
            '.phone-item',
            '.product-item',
            '.mobile-item'
        ]
        
        for selector in phone_indicators:
            if soup.select(selector):
                return True
        
        return False
