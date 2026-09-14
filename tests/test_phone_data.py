"""
Unit tests for phone data models and validation.

Tests the PhoneSpecifications dataclass, validation methods, and utility functions.
"""

import pytest
from datetime import datetime
from smartphone_specs_scraper.models.phone_data import (
    PhoneSpecifications, 
    PhoneDataValidator, 
    validate_phone_list
)


class TestPhoneSpecifications:
    """Test cases for PhoneSpecifications dataclass."""
    
    def test_phone_specifications_creation(self):
        """Test creating a PhoneSpecifications instance."""
        phone = PhoneSpecifications(
            brand="Samsung",
            model="Galaxy S21",
            device_type="Smartphone"
        )
        
        assert phone.brand == "Samsung"
        assert phone.model == "Galaxy S21"
        assert phone.device_type == "Smartphone"
        assert phone.operating_system is None  # Default value
    
    def test_to_dict_method(self):
        """Test converting PhoneSpecifications to dictionary."""
        phone = PhoneSpecifications(
            brand="Apple",
            model="iPhone 13",
            ram="6 GB",
            battery_capacity="3095 mAh"
        )
        
        result = phone.to_dict()
        
        assert isinstance(result, dict)
        assert result['brand'] == "Apple"
        assert result['model'] == "iPhone 13"
        assert result['ram'] == "6 GB"
        assert result['battery_capacity'] == "3095 mAh"
        assert 'operating_system' in result  # Should include None fields
    
    def test_validate_with_valid_data(self):
        """Test validation with valid phone data."""
        phone = PhoneSpecifications(
            brand="Xiaomi",
            model="Mi 11",
            detail_url="https://www.mobiledokan.com/xiaomi-mi-11",
            scraped_at="2024-01-15T10:30:00"
        )
        
        assert phone.validate() is True
    
    def test_validate_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        # Missing brand
        phone1 = PhoneSpecifications(model="Galaxy S21")
        assert phone1.validate() is False
        
        # Missing model
        phone2 = PhoneSpecifications(brand="Samsung")
        assert phone2.validate() is False
        
        # Missing both
        phone3 = PhoneSpecifications()
        assert phone3.validate() is False
    
    def test_validate_invalid_url(self):
        """Test validation fails with invalid URLs."""
        phone = PhoneSpecifications(
            brand="Samsung",
            model="Galaxy S21",
            detail_url="not-a-valid-url"
        )
        
        assert phone.validate() is False
    
    def test_validate_invalid_timestamp(self):
        """Test validation fails with invalid timestamp."""
        phone = PhoneSpecifications(
            brand="Samsung",
            model="Galaxy S21",
            scraped_at="invalid-timestamp"
        )
        
        assert phone.validate() is False
    
    def test_validate_valid_urls(self):
        """Test validation passes with valid URLs."""
        phone = PhoneSpecifications(
            brand="Samsung",
            model="Galaxy S21",
            detail_url="https://www.mobiledokan.com/samsung-galaxy-s21",
            image_url="https://www.mobiledokan.com/images/phone.jpg"
        )
        
        assert phone.validate() is True
    
    def test_is_valid_url_method(self):
        """Test URL validation method."""
        phone = PhoneSpecifications()
        
        # Valid URLs
        assert phone._is_valid_url("https://www.example.com") is True
        assert phone._is_valid_url("http://localhost:8000") is True
        assert phone._is_valid_url("https://mobiledokan.com/path/to/page") is True
        
        # Invalid URLs
        assert phone._is_valid_url("not-a-url") is False
        assert phone._is_valid_url("ftp://example.com") is False
        assert phone._is_valid_url("") is False


class TestPhoneDataValidator:
    """Test cases for PhoneDataValidator utility class."""
    
    def test_clean_text_normal_text(self):
        """Test cleaning normal text."""
        result = PhoneDataValidator.clean_text("  Samsung Galaxy S21  ")
        assert result == "Samsung Galaxy S21"
    
    def test_clean_text_multiple_spaces(self):
        """Test cleaning text with multiple spaces."""
        result = PhoneDataValidator.clean_text("Samsung    Galaxy     S21")
        assert result == "Samsung Galaxy S21"
    
    def test_clean_text_empty_values(self):
        """Test cleaning empty or N/A values."""
        assert PhoneDataValidator.clean_text("") is None
        assert PhoneDataValidator.clean_text("   ") is None
        assert PhoneDataValidator.clean_text("N/A") is None
        assert PhoneDataValidator.clean_text("not available") is None
        assert PhoneDataValidator.clean_text("-") is None
        assert PhoneDataValidator.clean_text(None) is None
    
    def test_clean_text_non_string(self):
        """Test cleaning non-string values."""
        assert PhoneDataValidator.clean_text(123) is None
        assert PhoneDataValidator.clean_text([]) is None
    
    def test_normalize_boolean_field_yes_values(self):
        """Test normalizing positive boolean values."""
        yes_values = ["yes", "Yes", "YES", "y", "true", "1", "available", "supported"]
        
        for value in yes_values:
            result = PhoneDataValidator.normalize_boolean_field(value)
            assert result == "Yes"
    
    def test_normalize_boolean_field_no_values(self):
        """Test normalizing negative boolean values."""
        no_values = ["no", "No", "NO", "n", "false", "0", "not available", "not supported"]
        
        for value in no_values:
            result = PhoneDataValidator.normalize_boolean_field(value)
            assert result == "No"
    
    def test_normalize_boolean_field_other_values(self):
        """Test normalizing other values."""
        result = PhoneDataValidator.normalize_boolean_field("Maybe")
        assert result == "Maybe"
        
        result = PhoneDataValidator.normalize_boolean_field(None)
        assert result is None
    
    def test_extract_numeric_value_simple(self):
        """Test extracting simple numeric values."""
        result = PhoneDataValidator.extract_numeric_value("128 GB")
        assert result == "128 GB"
        
        result = PhoneDataValidator.extract_numeric_value("6.1 inches")
        assert result == "6.1 inches"
    
    def test_extract_numeric_value_with_unit(self):
        """Test extracting numeric values and adding units."""
        result = PhoneDataValidator.extract_numeric_value("128", "GB")
        assert result == "128 GB"
        
        result = PhoneDataValidator.extract_numeric_value("6.1", "inches")
        assert result == "6.1 inches"
    
    def test_extract_numeric_value_no_numbers(self):
        """Test extracting from text with no numbers."""
        result = PhoneDataValidator.extract_numeric_value("No storage info")
        assert result is None
        
        result = PhoneDataValidator.extract_numeric_value(None)
        assert result is None
    
    def test_create_phone_from_dict(self):
        """Test creating PhoneSpecifications from dictionary."""
        data = {
            "brand": "  Samsung  ",
            "model": "Galaxy S21",
            "ram": "8 GB",
            "invalid_field": "should be ignored"
        }
        
        phone = PhoneDataValidator.create_phone_from_dict(data)
        
        assert phone.brand == "Samsung"  # Cleaned
        assert phone.model == "Galaxy S21"
        assert phone.ram == "8 GB"
        assert phone.scraped_at is not None  # Auto-added timestamp
    
    def test_create_phone_from_dict_with_na_values(self):
        """Test creating phone from dict with N/A values."""
        data = {
            "brand": "Samsung",
            "model": "Galaxy S21",
            "operating_system": "N/A",
            "ram": "not available"
        }
        
        phone = PhoneDataValidator.create_phone_from_dict(data)
        
        assert phone.brand == "Samsung"
        assert phone.model == "Galaxy S21"
        assert phone.operating_system is None  # N/A converted to None
        assert phone.ram is None  # "not available" converted to None
    
    def test_create_phone_from_dict_existing_timestamp(self):
        """Test creating phone from dict with existing timestamp."""
        timestamp = "2024-01-15T10:30:00"
        data = {
            "brand": "Samsung",
            "model": "Galaxy S21",
            "scraped_at": timestamp
        }
        
        phone = PhoneDataValidator.create_phone_from_dict(data)
        assert phone.scraped_at == timestamp


class TestValidatePhoneList:
    """Test cases for validate_phone_list function."""
    
    def test_validate_phone_list_all_valid(self):
        """Test validating list with all valid phones."""
        phones = [
            PhoneSpecifications(brand="Samsung", model="Galaxy S21"),
            PhoneSpecifications(brand="Apple", model="iPhone 13"),
            PhoneSpecifications(brand="Xiaomi", model="Mi 11")
        ]
        
        result = validate_phone_list(phones)
        assert len(result) == 3
        assert all(phone.validate() for phone in result)
    
    def test_validate_phone_list_mixed_validity(self):
        """Test validating list with mixed valid/invalid phones."""
        phones = [
            PhoneSpecifications(brand="Samsung", model="Galaxy S21"),  # Valid
            PhoneSpecifications(brand="Apple"),  # Invalid - no model
            PhoneSpecifications(model="Mi 11"),  # Invalid - no brand
            PhoneSpecifications(brand="OnePlus", model="9 Pro")  # Valid
        ]
        
        result = validate_phone_list(phones)
        assert len(result) == 2  # Only valid phones
        assert result[0].brand == "Samsung"
        assert result[1].brand == "OnePlus"
    
    def test_validate_phone_list_empty(self):
        """Test validating empty list."""
        result = validate_phone_list([])
        assert result == []
    
    def test_validate_phone_list_all_invalid(self):
        """Test validating list with all invalid phones."""
        phones = [
            PhoneSpecifications(),  # No brand or model
            PhoneSpecifications(brand="Samsung"),  # No model
            PhoneSpecifications(model="iPhone 13")  # No brand
        ]
        
        result = validate_phone_list(phones)
        assert len(result) == 0


class TestPhoneSpecificationsIntegration:
    """Integration tests for complete phone data workflow."""
    
    def test_complete_phone_data_workflow(self):
        """Test complete workflow from raw data to validated phone."""
        raw_data = {
            "brand": "  Samsung  ",
            "model": "Galaxy S21 Ultra",
            "device_type": "Smartphone",
            "operating_system": "Android",
            "os_version": "11",
            "ram": "12 GB",
            "internal_storage": "256 GB",
            "battery_capacity": "5000 mAh",
            "display_type": "Dynamic AMOLED 2X",
            "screen_size": "6.8 inches",
            "primary_camera_resolution": "108 MP",
            "detail_url": "https://www.mobiledokan.com/samsung-galaxy-s21-ultra",
            "waterproof": "yes",
            "face_unlock": "available"
        }
        
        # Create phone from raw data
        phone = PhoneDataValidator.create_phone_from_dict(raw_data)
        
        # Validate the phone
        assert phone.validate() is True
        
        # Convert to dict for export
        export_data = phone.to_dict()
        
        # Verify data integrity
        assert export_data['brand'] == "Samsung"  # Cleaned
        assert export_data['model'] == "Galaxy S21 Ultra"
        assert export_data['ram'] == "12 GB"
        assert export_data['detail_url'] == "https://www.mobiledokan.com/samsung-galaxy-s21-ultra"
        assert 'scraped_at' in export_data
        
        # Test in list validation
        phone_list = validate_phone_list([phone])
        assert len(phone_list) == 1
        assert phone_list[0] == phone