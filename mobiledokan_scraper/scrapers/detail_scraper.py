"""
Detail scraper for extracting comprehensive phone specifications from individual phone pages.

This module contains the DetailScraper class that handles parsing of phone detail pages
to extract all specification categories including General, Hardware, Display, Cameras,
Design, Battery, Memory, Network & Connectivity, Sensors & Security, Multimedia, and More.
"""

import logging
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup, Tag
import re
from datetime import datetime

from ..utils.http_client import HTTPClient
from ..models.phone_data import PhoneSpecifications, PhoneDataValidator
from ..utils.error_handling import ParsingError, handle_parsing_error, log_and_continue
from ..config.settings import SPEC_FIELD_MAPPINGS, DEFAULT_VALUES, DOMAIN


class DetailScraper:
    """
    Scraper for extracting detailed phone specifications from individual phone pages.
    
    This class handles the parsing of phone detail pages to extract comprehensive
    specifications organized by categories as defined in the requirements.
    """
    
    def __init__(self, http_client: HTTPClient):
        """
        Initialize the DetailScraper.
        
        Args:
            http_client (HTTPClient): HTTP client instance for making requests
        """
        self.http_client = http_client
        self.logger = logging.getLogger(__name__)
        
    def scrape_phone_details(self, phone_url: str, image_url: str = "") -> Optional[PhoneSpecifications]:
        """
        Scrape comprehensive phone specifications from a phone detail page.
        
        Args:
            phone_url (str): URL of the phone detail page
            image_url (str): URL of the phone image (optional)
            
        Returns:
            Optional[PhoneSpecifications]: Extracted phone specifications or None if failed
        """
        try:
            self.logger.info(f"Scraping phone details from: {phone_url}")
            
            # Make HTTP request to get the page content
            response = self.http_client.get(phone_url)
            if not response or response.status_code != 200:
                self.logger.error(f"Failed to fetch phone page: {phone_url}")
                return None
                
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract specifications from the page
            specifications = self.extract_specifications(soup)
            
            # Extract price information
            price_info = self.extract_price_information(soup)
            specifications.update(price_info)
            
            # Add metadata
            specifications['detail_url'] = phone_url
            specifications['image_url'] = image_url
            specifications['scraped_at'] = datetime.now().isoformat()
            
            # Create and validate phone specifications object
            phone_specs = PhoneDataValidator.create_phone_from_dict(specifications)
            
            if phone_specs.validate():
                self.logger.info(f"Successfully scraped specifications for: {phone_specs.brand} {phone_specs.model}")
                return phone_specs
            else:
                self.logger.warning(f"Validation failed for phone: {phone_url}")
                return phone_specs  # Return even if validation fails, let caller decide
                
        except Exception as e:
            self.logger.error(f"Error scraping phone details from {phone_url}: {str(e)}")
            return None
    
    def extract_specifications(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract all specifications from the parsed HTML.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            Dict[str, Any]: Dictionary containing all extracted specifications
        """
        specifications = {}
        
        try:
            # Find the main specifications section
            specs_section = soup.find('section', {'id': 'product-specs'})
            if not specs_section:
                self.logger.warning("No specifications section found")
                return specifications
            
            # Find all specification category rows
            spec_rows = specs_section.find_all('div', class_='row mb-2 pb-2 border-bottom')
            
            for row in spec_rows:
                category_specs = self._parse_specification_category(row)
                specifications.update(category_specs)
                
        except Exception as e:
            self.logger.error(f"Error extracting specifications: {str(e)}")
            
        return specifications
    
    def extract_price_information(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract all price-related information from the phone detail page.
        
        Handles multiple price formats including official/unofficial prices,
        discounted prices, variant prices, and update dates.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            Dict[str, Any]: Dictionary containing all price information
        """
        price_data = {
            'price_official': None,
            'price_unofficial': None,
            'price_old': None,
            'price_savings': None,
            'price_variants': [],
            'price_updated': None
        }
        
        try:
            # Find the price and variant container
            price_container = soup.find('div', class_='price-and-variant')
            if not price_container:
                self.logger.warning("No price container found")
                return price_data
            
            # Extract official and unofficial prices
            self._extract_main_prices(price_container, price_data)
            
            # Extract old/discounted price information
            self._extract_discount_info(price_container, price_data)
            
            # Extract variant prices
            self._extract_variant_prices(price_container, price_data)
            
            # Extract price update date
            self._extract_price_update_date(price_container, price_data)
            
        except Exception as e:
            self.logger.error(f"Error extracting price information: {str(e)}")
            
        return price_data
    
    def _extract_main_prices(self, container: Tag, price_data: Dict[str, Any]) -> None:
        """Extract official and unofficial prices from the main price section."""
        try:
            # Find all price elements with tags
            price_elements = container.find_all('span', class_='fw-bold')
            
            for element in price_elements:
                price_text = element.get_text(strip=True)
                
                # Check for official price pattern
                if '(Official)' in price_text:
                    price_value = self._extract_price_value(price_text)
                    if price_value:
                        price_data['price_official'] = price_value
                
                # Check for unofficial price pattern
                elif '(Unofficial)' in price_text:
                    price_value = self._extract_price_value(price_text)
                    if price_value:
                        price_data['price_unofficial'] = price_value
                        
        except Exception as e:
            self.logger.error(f"Error extracting main prices: {str(e)}")
    
    def _extract_discount_info(self, container: Tag, price_data: Dict[str, Any]) -> None:
        """Extract old price and savings information."""
        try:
            # Look for old price (crossed out)
            old_price_element = container.find('span', class_='old-price')
            if old_price_element:
                old_price = self._extract_price_value(old_price_element.get_text(strip=True))
                if old_price:
                    price_data['price_old'] = old_price
            
            # Look for savings information
            savings_element = container.find('span', class_='saved-amount')
            if savings_element:
                savings_text = savings_element.get_text(strip=True)
                # Also look for percentage
                percentage_element = container.find('span', class_='saved-percentage')
                if percentage_element:
                    percentage_text = percentage_element.get_text(strip=True)
                    savings_text += f" {percentage_text}"
                
                price_data['price_savings'] = savings_text
                
        except Exception as e:
            self.logger.error(f"Error extracting discount info: {str(e)}")
    
    def _extract_variant_prices(self, container: Tag, price_data: Dict[str, Any]) -> None:
        """Extract variant prices from the variant section."""
        try:
            # Find variant container
            variant_container = container.find('div', class_='varsti')
            if not variant_container:
                return
            
            # Find all variant links
            variant_links = variant_container.find_all('a', class_='rounded')
            
            variants = []
            for link in variant_links:
                try:
                    # Extract variant specification (e.g., "512GB", "12GB+512GB")
                    variant_spec_element = link.find('span', class_='vtst')
                    variant_spec = variant_spec_element.get_text(strip=True) if variant_spec_element else ""
                    
                    # Extract variant price
                    variant_price_element = link.find('span', class_='ptst')
                    variant_price = ""
                    if variant_price_element:
                        variant_price = self._extract_price_value(variant_price_element.get_text(strip=True))
                    
                    if variant_spec and variant_price:
                        variants.append({
                            'variant': variant_spec,
                            'price': variant_price
                        })
                        
                except Exception as e:
                    self.logger.error(f"Error parsing variant: {str(e)}")
                    continue
            
            if variants:
                price_data['price_variants'] = variants
                
        except Exception as e:
            self.logger.error(f"Error extracting variant prices: {str(e)}")
    
    def _extract_price_update_date(self, container: Tag, price_data: Dict[str, Any]) -> None:
        """Extract the price update date."""
        try:
            # Look for update date
            update_element = container.find('span', class_='updat')
            if update_element:
                update_text = update_element.get_text(strip=True)
                # Extract date from "Updated on: June 6, 2025" format
                date_match = re.search(r'Updated on:\s*(.+)', update_text)
                if date_match:
                    price_data['price_updated'] = date_match.group(1).strip()
                    
        except Exception as e:
            self.logger.error(f"Error extracting price update date: {str(e)}")
    
    def _extract_price_value(self, price_text: str) -> Optional[str]:
        """
        Extract numeric price value from price text.
        
        Args:
            price_text (str): Raw price text (e.g., "৳.43,999 (Official)")
            
        Returns:
            Optional[str]: Cleaned price value (e.g., "43,999") or None
        """
        try:
            # Remove currency symbols and tags
            cleaned_text = re.sub(r'[৳.]', '', price_text)
            cleaned_text = re.sub(r'\(Official\)|\(Unofficial\)', '', cleaned_text)
            
            # Extract numeric value with commas
            price_match = re.search(r'([\d,]+)', cleaned_text.strip())
            if price_match:
                return price_match.group(1)
                
        except Exception as e:
            self.logger.error(f"Error extracting price value from '{price_text}': {str(e)}")
            
        return None
    
    def _parse_specification_category(self, row: Tag) -> Dict[str, str]:
        """
        Parse a single specification category row.
        
        Args:
            row (Tag): BeautifulSoup tag representing a specification category row
            
        Returns:
            Dict[str, str]: Dictionary of specifications for this category
        """
        category_specs = {}
        
        try:
            # Find the category name
            category_header = row.find('h3', class_='text-bold')
            category_name = category_header.get_text(strip=True) if category_header else "Unknown"
            
            # Find the specification table for this category
            spec_table = row.find('table', class_='spec-grp-tbl')
            if not spec_table:
                self.logger.debug(f"No specification table found for category: {category_name}")
                return category_specs
            
            # Parse all specification rows in the table
            spec_rows = spec_table.find_all('tr')
            for spec_row in spec_rows:
                spec_data = self._parse_specification_row(spec_row)
                if spec_data:
                    category_specs.update(spec_data)
                    
        except Exception as e:
            self.logger.error(f"Error parsing specification category: {str(e)}")
            
        return category_specs
    
    def _parse_specification_row(self, row: Tag) -> Optional[Dict[str, str]]:
        """
        Parse a single specification row to extract field name and value.
        
        Args:
            row (Tag): BeautifulSoup tag representing a specification row
            
        Returns:
            Optional[Dict[str, str]]: Dictionary with field name and value or None
        """
        try:
            # Find the two cells in the row
            cells = row.find_all('td')
            if len(cells) != 2:
                return None
            
            # Extract field name and value
            field_name = cells[0].get_text(strip=True)
            field_value = self._extract_cell_value(cells[1])
            
            if not field_name or not field_value:
                return None
            
            # Map field name to our data model field
            mapped_field = SPEC_FIELD_MAPPINGS.get(field_name)
            if not mapped_field:
                self.logger.debug(f"Unknown field: {field_name}")
                return None
            
            # Clean and normalize the value
            cleaned_value = PhoneDataValidator.clean_text(field_value)
            if not cleaned_value:
                return None
            
            return {mapped_field: cleaned_value}
            
        except Exception as e:
            self.logger.error(f"Error parsing specification row: {str(e)}")
            return None
    
    def _extract_cell_value(self, cell: Tag) -> str:
        """
        Extract text value from a table cell, handling various HTML structures.
        
        Args:
            cell (Tag): BeautifulSoup tag representing a table cell
            
        Returns:
            str: Extracted text value
        """
        try:
            # Create a copy to avoid modifying the original
            cell_copy = BeautifulSoup(str(cell), 'html.parser').find()
            
            # Remove any SVG icons or other non-text elements
            for svg in cell_copy.find_all('svg'):
                svg.decompose()
            
            # Get all text content
            full_text = cell_copy.get_text(separator=' ', strip=True)
            
            # Clean up common patterns
            full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces to single space
            full_text = full_text.strip()
            
            return full_text
            
        except Exception as e:
            self.logger.error(f"Error extracting cell value: {str(e)}")
            return ""
    
    def _normalize_specification_value(self, field_name: str, value: str) -> str:
        """
        Normalize specification values based on field type.
        
        Args:
            field_name (str): Name of the specification field
            value (str): Raw value to normalize
            
        Returns:
            str: Normalized value
        """
        if not value:
            return ""
        
        # Boolean-like fields
        boolean_fields = [
            'waterproof', 'usb_type_c', 'usb_otg', 'wifi_hotspot', 
            'face_unlock', 'bezel_less_display', 'touch_screen'
        ]
        
        if field_name in boolean_fields:
            return PhoneDataValidator.normalize_boolean_field(value) or value
        
        # Numeric fields that might need unit extraction
        numeric_fields = {
            'screen_size': 'inches',
            'pixel_density': 'ppi',
            'brightness': 'nits',
            'refresh_rate': 'Hz',
            'battery_capacity': 'mAh',
            'weight': 'g',
            'thickness': 'mm',
            'height': 'mm',
            'width': 'mm'
        }
        
        if field_name in numeric_fields:
            extracted = PhoneDataValidator.extract_numeric_value(value, numeric_fields[field_name])
            return extracted or value
        
        # Default: just clean the text
        return PhoneDataValidator.clean_text(value) or value