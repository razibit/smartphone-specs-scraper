"""
Phone data models and validation utilities.

This module contains the PhoneSpecifications dataclass and related validation
methods for handling scraped phone data from MobileDokan.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
import re


@dataclass
class PhoneSpecifications:
    """
    Data model for phone specifications scraped from MobileDokan.
    
    Contains all specification fields organized by categories as defined
    in the requirements document.
    """
    
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
    user_interface: Optional[str] = None
    chipset: Optional[str] = None
    cpu: Optional[str] = None
    cpu_cores: Optional[str] = None
    architecture: Optional[str] = None
    fabrication: Optional[str] = None
    gpu: Optional[str] = None
    
    # Display
    display_type: Optional[str] = None
    screen_size: Optional[str] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    pixel_density: Optional[str] = None
    screen_to_body_ratio: Optional[str] = None
    screen_protection: Optional[str] = None
    bezel_less_display: Optional[str] = None
    touch_screen: Optional[str] = None
    brightness: Optional[str] = None
    refresh_rate: Optional[str] = None
    notch: Optional[str] = None
    
    # Cameras
    primary_camera_setup: Optional[str] = None
    primary_camera_resolution: Optional[str] = None
    primary_camera_autofocus: Optional[str] = None
    primary_camera_flash: Optional[str] = None
    primary_camera_image_resolution: Optional[str] = None
    primary_camera_settings: Optional[str] = None
    primary_camera_zoom: Optional[str] = None
    primary_camera_shooting_modes: Optional[str] = None
    primary_camera_features: Optional[str] = None
    primary_camera_video_recording: Optional[str] = None
    primary_camera_video_fps: Optional[str] = None
    selfie_camera_setup: Optional[str] = None
    selfie_camera_resolution: Optional[str] = None
    
    # Design
    height: Optional[str] = None
    width: Optional[str] = None
    thickness: Optional[str] = None
    weight: Optional[str] = None
    colors: Optional[str] = None
    waterproof: Optional[str] = None
    ip_rating: Optional[str] = None
    ruggedness: Optional[str] = None
    
    # Battery
    battery_type: Optional[str] = None
    battery_capacity: Optional[str] = None
    quick_charging: Optional[str] = None
    battery_placement: Optional[str] = None
    usb_type_c: Optional[str] = None
    
    # Memory
    internal_storage: Optional[str] = None
    storage_type: Optional[str] = None
    expandable_memory: Optional[str] = None
    usb_otg: Optional[str] = None
    ram: Optional[str] = None
    ram_type: Optional[str] = None
    
    # Network & Connectivity
    network: Optional[str] = None
    sim_slot: Optional[str] = None
    sim_size: Optional[str] = None
    edge: Optional[str] = None
    gprs: Optional[str] = None
    volte: Optional[str] = None
    speed: Optional[str] = None
    wlan: Optional[str] = None
    bluetooth: Optional[str] = None
    gps: Optional[str] = None
    wifi_hotspot: Optional[str] = None
    usb: Optional[str] = None
    
    # Sensors & Security
    sensors: Optional[str] = None
    face_unlock: Optional[str] = None
    
    # Multimedia
    loudspeaker: Optional[str] = None
    audio_jack: Optional[str] = None
    video: Optional[str] = None
    
    # More
    made_by: Optional[str] = None
    features: Optional[str] = None
    
    # Metadata
    image_url: Optional[str] = None
    detail_url: Optional[str] = None
    scraped_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the PhoneSpecifications instance to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation suitable for JSON/CSV export
        """
        return asdict(self)
    
    def validate(self) -> bool:
        """
        Validate the phone specifications data.
        
        Performs basic validation checks on the data to ensure it meets
        minimum requirements for a valid phone record.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        # Check if at least brand and model are present (minimum required fields)
        if not self.brand or not self.model:
            return False
            
        # Validate scraped_at timestamp format if present
        if self.scraped_at:
            try:
                datetime.fromisoformat(self.scraped_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return False
        
        # Validate URL format if present
        if self.detail_url and not self._is_valid_url(self.detail_url):
            return False
            
        if self.image_url and not self._is_valid_url(self.image_url):
            return False
            
        return True
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a string is a valid URL format.
        
        Args:
            url (str): URL string to validate
            
        Returns:
            bool: True if URL format is valid, False otherwise
        """
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None


class PhoneDataValidator:
    """
    Utility class for validating and converting phone specification data.
    """
    
    @staticmethod
    def clean_text(text: Optional[str]) -> Optional[str]:
        """
        Clean and normalize text data.
        
        Args:
            text (Optional[str]): Raw text to clean
            
        Returns:
            Optional[str]: Cleaned text or None if empty
        """
        if not text or not isinstance(text, str):
            return None
            
        # Remove extra whitespace and normalize
        cleaned = ' '.join(text.strip().split())
        
        # Return None for empty strings or common "not available" indicators
        if not cleaned or cleaned.lower() in ['n/a', 'na', 'not available', '-', '']:
            return None
            
        return cleaned
    
    @staticmethod
    def normalize_boolean_field(value: Optional[str]) -> Optional[str]:
        """
        Normalize boolean-like fields to consistent values.
        
        Args:
            value (Optional[str]): Raw value to normalize
            
        Returns:
            Optional[str]: Normalized value ('Yes', 'No', or None)
        """
        if not value:
            return None
            
        value_lower = value.lower().strip()
        
        if value_lower in ['yes', 'y', 'true', '1', 'available', 'supported']:
            return 'Yes'
        elif value_lower in ['no', 'n', 'false', '0', 'not available', 'not supported']:
            return 'No'
        else:
            return PhoneDataValidator.clean_text(value)
    
    @staticmethod
    def extract_numeric_value(text: Optional[str], unit: str = '') -> Optional[str]:
        """
        Extract numeric values from text with optional unit preservation.
        
        Args:
            text (Optional[str]): Text containing numeric value
            unit (str): Expected unit to preserve
            
        Returns:
            Optional[str]: Extracted numeric value with unit or None
        """
        if not text:
            return None
            
        # Extract numbers (including decimals) from text
        numbers = re.findall(r'\d+\.?\d*', text)
        if not numbers:
            return None
            
        # Take the first number found
        numeric_value = numbers[0]
        
        # Add unit if specified and not already present
        if unit and unit.lower() not in text.lower():
            return f"{numeric_value} {unit}"
        
        return PhoneDataValidator.clean_text(text)
    
    @staticmethod
    def create_phone_from_dict(data: Dict[str, Any]) -> PhoneSpecifications:
        """
        Create a PhoneSpecifications instance from a dictionary with data cleaning.
        
        Args:
            data (Dict[str, Any]): Raw data dictionary
            
        Returns:
            PhoneSpecifications: Cleaned and validated phone specifications
        """
        # Get valid field names from PhoneSpecifications
        valid_fields = set(PhoneSpecifications.__dataclass_fields__.keys())
        
        # Clean all text fields and filter valid fields only
        cleaned_data = {}
        for key, value in data.items():
            if key in valid_fields:
                if isinstance(value, str):
                    cleaned_data[key] = PhoneDataValidator.clean_text(value)
                else:
                    cleaned_data[key] = value
        
        # Add scraped timestamp if not present
        if 'scraped_at' not in cleaned_data or not cleaned_data['scraped_at']:
            cleaned_data['scraped_at'] = datetime.now().isoformat()
        
        # Create instance with cleaned data
        return PhoneSpecifications(**cleaned_data)


def validate_phone_list(phones: List[PhoneSpecifications]) -> List[PhoneSpecifications]:
    """
    Validate a list of phone specifications and return only valid ones.
    
    Args:
        phones (List[PhoneSpecifications]): List of phone specifications to validate
        
    Returns:
        List[PhoneSpecifications]: List of valid phone specifications
    """
    valid_phones = []
    for phone in phones:
        if phone.validate():
            valid_phones.append(phone)
    
    return valid_phones