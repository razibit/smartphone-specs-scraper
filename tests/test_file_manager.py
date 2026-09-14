"""
Unit tests for FileManager class.

Tests file operations, data formatting, and error handling for JSON and CSV export.
"""

import pytest
import json
import csv
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open

from smartphone_specs_scraper.utils.file_manager import FileManager
from smartphone_specs_scraper.models.phone_data import PhoneSpecifications


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def file_manager(temp_dir):
    """Create FileManager instance with temporary directory."""
    return FileManager(output_dir=str(temp_dir))


@pytest.fixture
def sample_phone_data():
    """Sample phone data for testing."""
    return [
        {
            'brand': 'Samsung',
            'model': 'Galaxy S21',
            'device_type': 'Smartphone',
            'release_date': '2021-01-29',
            'status': 'Available',
            'operating_system': 'Android',
            'os_version': '11',
            'display_type': 'Dynamic AMOLED',
            'screen_size': '6.2 inches',
            'ram': '8 GB',
            'internal_storage': '128 GB',
            'image_url': 'https://example.com/image.jpg',
            'detail_url': 'https://example.com/phone/samsung-galaxy-s21',
            'scraped_at': '2024-01-28T14:30:52'
        },
        {
            'brand': 'Apple',
            'model': 'iPhone 13',
            'device_type': 'Smartphone',
            'release_date': '2021-09-24',
            'status': 'Available',
            'operating_system': 'iOS',
            'os_version': '15',
            'display_type': 'Super Retina XDR',
            'screen_size': '6.1 inches',
            'ram': '6 GB',
            'internal_storage': '128 GB',
            'image_url': 'https://example.com/iphone.jpg',
            'detail_url': 'https://example.com/phone/apple-iphone-13',
            'scraped_at': '2024-01-28T14:31:15'
        }
    ]


@pytest.fixture
def sample_phone_specifications():
    """Sample PhoneSpecifications objects for testing."""
    return [
        PhoneSpecifications(
            brand='Samsung',
            model='Galaxy S21',
            device_type='Smartphone',
            release_date='2021-01-29',
            status='Available',
            operating_system='Android',
            os_version='11',
            display_type='Dynamic AMOLED',
            screen_size='6.2 inches',
            ram='8 GB',
            internal_storage='128 GB',
            image_url='https://example.com/image.jpg',
            detail_url='https://example.com/phone/samsung-galaxy-s21',
            scraped_at='2024-01-28T14:30:52'
        ),
        PhoneSpecifications(
            brand='Apple',
            model='iPhone 13',
            device_type='Smartphone',
            release_date='2021-09-24',
            status='Available',
            operating_system='iOS',
            os_version='15',
            display_type='Super Retina XDR',
            screen_size='6.1 inches',
            ram='6 GB',
            internal_storage='128 GB',
            image_url='https://example.com/iphone.jpg',
            detail_url='https://example.com/phone/apple-iphone-13',
            scraped_at='2024-01-28T14:31:15'
        )
    ]


class TestFileManager:
    """Test cases for FileManager class."""


class TestFileManagerInitialization:
    """Test FileManager initialization and directory management."""
    
    def test_init_with_default_directory(self):
        """Test initialization with default output directory."""
        with patch('smartphone_specs_scraper.utils.file_manager.Path.mkdir') as mock_mkdir:
            file_manager = FileManager()
            assert file_manager.output_dir.name == 'output'
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_init_with_custom_directory(self, temp_dir):
        """Test initialization with custom output directory."""
        custom_dir = temp_dir / 'custom_output'
        file_manager = FileManager(output_dir=str(custom_dir))
        assert file_manager.output_dir == custom_dir
        assert custom_dir.exists()
    
    def test_create_output_directory_success(self, temp_dir):
        """Test successful output directory creation."""
        output_dir = temp_dir / 'test_output'
        file_manager = FileManager(output_dir=str(output_dir))
        assert output_dir.exists()
        assert output_dir.is_dir()
    
    def test_create_output_directory_failure(self):
        """Test handling of directory creation failure."""
        with patch('smartphone_specs_scraper.utils.file_manager.Path.mkdir', side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                FileManager(output_dir='/invalid/path')


class TestFilenameGeneration:
    """Test filename generation methods."""
    
    def test_generate_filename_with_timestamp(self, file_manager):
        """Test filename generation with timestamp."""
        with patch('smartphone_specs_scraper.utils.file_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240128_143052'
            
            filename = file_manager.generate_filename('test', 'json')
            assert filename == 'test_20240128_143052.json'
    
    def test_generate_filename_without_timestamp(self, file_manager):
        """Test filename generation without timestamp."""
        filename = file_manager.generate_filename('test', 'csv', include_timestamp=False)
        assert filename == 'test.csv'
    
    def test_generate_filename_extension_handling(self, file_manager):
        """Test proper handling of file extensions."""
        # Extension without dot
        filename1 = file_manager.generate_filename('test', 'json', include_timestamp=False)
        assert filename1 == 'test.json'
        
        # Extension with dot
        filename2 = file_manager.generate_filename('test', '.csv', include_timestamp=False)
        assert filename2 == 'test.csv'
    
    def test_get_output_path(self, file_manager):
        """Test output path generation."""
        path = file_manager.get_output_path('test.json')
        assert path.name == 'test.json'
        assert path.parent == file_manager.output_dir


class TestJSONExport:
    """Test JSON export functionality."""
    
    def test_save_to_json_success(self, file_manager, sample_phone_data):
        """Test successful JSON file saving."""
        output_path = file_manager.save_to_json(sample_phone_data, 'test.json', include_timestamp=False)
        
        assert output_path.exists()
        assert output_path.suffix == '.json'
        
        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 2
        assert saved_data[0]['brand'] == 'Samsung'
        assert saved_data[1]['brand'] == 'Apple'
    
    def test_save_to_json_with_timestamp(self, file_manager, sample_phone_data):
        """Test JSON saving with timestamp in filename."""
        with patch('smartphone_specs_scraper.utils.file_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240128_143052'
            
            output_path = file_manager.save_to_json(sample_phone_data)
            assert '20240128_143052' in output_path.name
    
    def test_save_to_json_empty_data(self, file_manager):
        """Test JSON saving with empty data."""
        with pytest.raises(ValueError, match="Cannot save empty data to JSON"):
            file_manager.save_to_json([])
    
    def test_save_to_json_with_none_values(self, file_manager):
        """Test JSON saving with None values."""
        data = [{'brand': 'Samsung', 'model': None, 'ram': '8 GB'}]
        output_path = file_manager.save_to_json(data, 'test_none.json', include_timestamp=False)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data[0]['model'] is None
    
    def test_save_to_json_file_write_error(self, file_manager, sample_phone_data):
        """Test handling of file write errors."""
        with patch('builtins.open', side_effect=IOError("Disk full")):
            with pytest.raises(IOError):
                file_manager.save_to_json(sample_phone_data, 'test.json')


class TestCSVExport:
    """Test CSV export functionality."""
    
    def test_save_to_csv_success(self, file_manager, sample_phone_data):
        """Test successful CSV file saving."""
        output_path = file_manager.save_to_csv(sample_phone_data, 'test.csv', include_timestamp=False)
        
        assert output_path.exists()
        assert output_path.suffix == '.csv'
        
        # Verify content
        with open(output_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['brand'] == 'Samsung'
        assert rows[1]['brand'] == 'Apple'
    
    def test_save_to_csv_with_timestamp(self, file_manager, sample_phone_data):
        """Test CSV saving with timestamp in filename."""
        with patch('smartphone_specs_scraper.utils.file_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240128_143052'
            
            output_path = file_manager.save_to_csv(sample_phone_data)
            assert '20240128_143052' in output_path.name
    
    def test_save_to_csv_empty_data(self, file_manager):
        """Test CSV saving with empty data."""
        with pytest.raises(ValueError, match="Cannot save empty data to CSV"):
            file_manager.save_to_csv([])
    
    def test_save_to_csv_field_ordering(self, file_manager, sample_phone_data):
        """Test CSV field ordering with priority fields first."""
        output_path = file_manager.save_to_csv(sample_phone_data, 'test_order.csv', include_timestamp=False)
        
        with open(output_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
        
        # Check that priority fields come first
        priority_fields = ['brand', 'model', 'device_type', 'release_date', 'status']
        for i, field in enumerate(priority_fields):
            assert headers[i] == field
    
    def test_save_to_csv_with_none_values(self, file_manager):
        """Test CSV saving with None values."""
        data = [{'brand': 'Samsung', 'model': None, 'ram': '8 GB'}]
        output_path = file_manager.save_to_csv(data, 'test_none.csv', include_timestamp=False)
        
        with open(output_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            row = next(reader)
        
        assert row['model'] == ''  # None should become empty string
    
    def test_save_to_csv_with_boolean_values(self, file_manager):
        """Test CSV saving with boolean values."""
        data = [{'brand': 'Samsung', 'waterproof': True, 'expandable': False}]
        output_path = file_manager.save_to_csv(data, 'test_bool.csv', include_timestamp=False)
        
        with open(output_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            row = next(reader)
        
        assert row['waterproof'] == 'Yes'
        assert row['expandable'] == 'No'
    
    def test_save_to_csv_file_write_error(self, file_manager, sample_phone_data):
        """Test handling of CSV file write errors."""
        with patch('builtins.open', side_effect=IOError("Disk full")):
            with pytest.raises(IOError):
                file_manager.save_to_csv(sample_phone_data, 'test.csv')


class TestPhoneSpecificationsExport:
    """Test export of PhoneSpecifications objects."""
    
    def test_save_phone_specifications_success(self, file_manager, sample_phone_specifications):
        """Test successful saving of phone specifications to both formats."""
        paths = file_manager.save_phone_specifications(
            sample_phone_specifications, 
            'test_phones', 
            include_timestamp=False
        )
        
        assert 'json' in paths
        assert 'csv' in paths
        assert paths['json'].exists()
        assert paths['csv'].exists()
        assert paths['json'].suffix == '.json'
        assert paths['csv'].suffix == '.csv'
    
    def test_save_phone_specifications_with_timestamp(self, file_manager, sample_phone_specifications):
        """Test saving phone specifications with timestamp."""
        with patch('smartphone_specs_scraper.utils.file_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240128_143052'
            
            paths = file_manager.save_phone_specifications(sample_phone_specifications)
            
            assert '20240128_143052' in paths['json'].name
            assert '20240128_143052' in paths['csv'].name
    
    def test_save_phone_specifications_empty_list(self, file_manager):
        """Test saving empty phone specifications list."""
        with pytest.raises(ValueError, match="Cannot save empty phone specifications list"):
            file_manager.save_phone_specifications([])
    
    def test_save_phone_specifications_data_conversion(self, file_manager, sample_phone_specifications):
        """Test that phone specifications are properly converted to dictionaries."""
        paths = file_manager.save_phone_specifications(
            sample_phone_specifications, 
            'test_conversion', 
            include_timestamp=False
        )
        
        # Verify JSON content
        with open(paths['json'], 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        assert len(json_data) == 2
        assert json_data[0]['brand'] == 'Samsung'
        assert json_data[1]['brand'] == 'Apple'
        
        # Verify CSV content
        with open(paths['csv'], 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            csv_data = list(reader)
        
        assert len(csv_data) == 2
        assert csv_data[0]['brand'] == 'Samsung'
        assert csv_data[1]['brand'] == 'Apple'


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_list_output_files_empty_directory(self, file_manager):
        """Test listing files in empty directory."""
        files = file_manager.list_output_files()
        assert files == []
    
    def test_list_output_files_with_files(self, file_manager, sample_phone_data):
        """Test listing files in directory with files."""
        # Create some test files
        file_manager.save_to_json(sample_phone_data, 'test1.json', include_timestamp=False)
        file_manager.save_to_csv(sample_phone_data, 'test1.csv', include_timestamp=False)
        
        files = file_manager.list_output_files()
        assert len(files) == 2
        
        json_files = file_manager.list_output_files('*.json')
        assert len(json_files) == 1
        assert json_files[0].suffix == '.json'
    
    def test_cleanup_old_files(self, file_manager, sample_phone_data):
        """Test cleanup of old files."""
        # Create multiple files with different timestamps
        for i in range(7):
            filename = f'test_{i}.json'
            file_manager.save_to_json(sample_phone_data, filename, include_timestamp=False)
        
        # Cleanup, keeping only 3 files
        deleted_count = file_manager.cleanup_old_files(keep_count=3, pattern='*.json')
        
        assert deleted_count == 4  # Should delete 4 files (7 - 3)
        
        remaining_files = file_manager.list_output_files('*.json')
        assert len(remaining_files) == 3
    
    def test_cleanup_old_files_insufficient_files(self, file_manager, sample_phone_data):
        """Test cleanup when there are fewer files than keep_count."""
        # Create only 2 files
        file_manager.save_to_json(sample_phone_data, 'test1.json', include_timestamp=False)
        file_manager.save_to_json(sample_phone_data, 'test2.json', include_timestamp=False)
        
        # Try to keep 5 files
        deleted_count = file_manager.cleanup_old_files(keep_count=5, pattern='*.json')
        
        assert deleted_count == 0  # Should delete no files
        
        remaining_files = file_manager.list_output_files('*.json')
        assert len(remaining_files) == 2


class TestDataFormatting:
    """Test data formatting methods."""
    
    def test_prepare_data_for_json(self, file_manager):
        """Test JSON data preparation."""
        data = [
            {'brand': 'Samsung', 'model': None, 'available': True, 'price': 999.99},
            {'brand': 'Apple', 'model': 'iPhone', 'available': False, 'price': 1099}
        ]
        
        prepared = file_manager._prepare_data_for_json(data)
        
        assert prepared[0]['model'] is None
        assert prepared[0]['available'] is True
        assert prepared[0]['price'] == 999.99
        assert prepared[1]['available'] is False
    
    def test_get_csv_fieldnames(self, file_manager):
        """Test CSV fieldname extraction and ordering."""
        data = [
            {'model': 'Galaxy', 'brand': 'Samsung', 'ram': '8GB'},
            {'brand': 'Apple', 'storage': '128GB', 'model': 'iPhone'}
        ]
        
        fieldnames = file_manager._get_csv_fieldnames(data)
        
        # Check that priority fields come first
        assert fieldnames[0] == 'brand'
        assert fieldnames[1] == 'model'
        # Check that all fields are included
        assert 'ram' in fieldnames
        assert 'storage' in fieldnames
    
    def test_prepare_row_for_csv(self, file_manager):
        """Test CSV row preparation."""
        row = {'brand': 'Samsung', 'model': None, 'available': True, 'discontinued': False}
        fieldnames = ['brand', 'model', 'available', 'discontinued', 'price']
        
        prepared = file_manager._prepare_row_for_csv(row, fieldnames)
        
        assert prepared['brand'] == 'Samsung'
        assert prepared['model'] == ''  # None becomes empty string
        assert prepared['available'] == 'Yes'  # True becomes 'Yes'
        assert prepared['discontinued'] == 'No'  # False becomes 'No'
        assert prepared['price'] == ''  # Missing field becomes empty string


if __name__ == '__main__':
    pytest.main([__file__])