"""
File management utilities for data export.

This module provides the FileManager class for handling JSON and CSV data export
with proper directory management, timestamp-based filenames, and data formatting.
"""

import os
import json
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..config.settings import OUTPUT_DIR, JSON_FILENAME, CSV_FILENAME, JSON_ENCODING, CSV_ENCODING
from ..models.phone_data import PhoneSpecifications


logger = logging.getLogger(__name__)


class FileManager:
    """
    Handles file operations for exporting scraped phone data.
    
    Provides methods for saving data in JSON and CSV formats with proper
    directory management and timestamp-based filename generation.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize FileManager with output directory.
        
        Args:
            output_dir (Optional[str]): Custom output directory path.
                                      Defaults to settings.OUTPUT_DIR if None.
        """
        self.output_dir = Path(output_dir or OUTPUT_DIR)
        self.create_output_directory()
    
    def create_output_directory(self) -> None:
        """
        Create the output directory if it doesn't exist.
        
        Creates the directory structure recursively and logs the operation.
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory ensured: {self.output_dir}")
        except OSError as e:
            logger.error(f"Failed to create output directory {self.output_dir}: {e}")
            raise
    
    def generate_filename(self, base_name: str, extension: str, include_timestamp: bool = True) -> str:
        """
        Generate a filename with optional timestamp.
        
        Args:
            base_name (str): Base name for the file (without extension)
            extension (str): File extension (with or without leading dot)
            include_timestamp (bool): Whether to include timestamp in filename
            
        Returns:
            str: Generated filename with timestamp if requested
            
        Example:
            generate_filename("phones_data", "json") -> "phones_data_20240128_143052.json"
            generate_filename("phones_data", ".csv", False) -> "phones_data.csv"
        """
        # Ensure extension has leading dot
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{base_name}_{timestamp}{extension}"
        else:
            return f"{base_name}{extension}"
    
    def get_output_path(self, filename: str) -> Path:
        """
        Get the full path for an output file.
        
        Args:
            filename (str): Name of the file
            
        Returns:
            Path: Full path to the output file
        """
        return self.output_dir / filename
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: Optional[str] = None, 
                     include_timestamp: bool = True, indent: int = 2) -> Path:
        """
        Save data to JSON format.
        
        Args:
            data (List[Dict[str, Any]]): List of phone data dictionaries to save
            filename (Optional[str]): Custom filename. Uses default if None.
            include_timestamp (bool): Whether to include timestamp in filename
            indent (int): JSON indentation level for pretty printing
            
        Returns:
            Path: Path to the saved file
            
        Raises:
            ValueError: If data is empty or invalid
            IOError: If file writing fails
        """
        if not data:
            raise ValueError("Cannot save empty data to JSON")
        
        if filename is None:
            base_name = JSON_FILENAME.rsplit('.', 1)[0]  # Remove extension
            filename = self.generate_filename(base_name, 'json', include_timestamp)
        
        output_path = self.get_output_path(filename)
        
        try:
            # Prepare data for JSON serialization
            json_data = self._prepare_data_for_json(data)
            
            with open(output_path, 'w', encoding=JSON_ENCODING) as f:
                json.dump(json_data, f, indent=indent, ensure_ascii=False, default=str)
            
            logger.info(f"Successfully saved {len(data)} records to JSON: {output_path}")
            return output_path
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to save JSON file {output_path}: {e}")
            raise
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize data to JSON: {e}")
            raise
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: Optional[str] = None,
                    include_timestamp: bool = True) -> Path:
        """
        Save data to CSV format.
        
        Args:
            data (List[Dict[str, Any]]): List of phone data dictionaries to save
            filename (Optional[str]): Custom filename. Uses default if None.
            include_timestamp (bool): Whether to include timestamp in filename
            
        Returns:
            Path: Path to the saved file
            
        Raises:
            ValueError: If data is empty or invalid
            IOError: If file writing fails
        """
        if not data:
            raise ValueError("Cannot save empty data to CSV")
        
        if filename is None:
            base_name = CSV_FILENAME.rsplit('.', 1)[0]  # Remove extension
            filename = self.generate_filename(base_name, 'csv', include_timestamp)
        
        output_path = self.get_output_path(filename)
        
        try:
            # Get all unique field names from the data
            fieldnames = self._get_csv_fieldnames(data)
            
            with open(output_path, 'w', newline='', encoding=CSV_ENCODING) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                # Write data rows with proper formatting
                for row in data:
                    formatted_row = self._prepare_row_for_csv(row, fieldnames)
                    writer.writerow(formatted_row)
            
            logger.info(f"Successfully saved {len(data)} records to CSV: {output_path}")
            return output_path
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to save CSV file {output_path}: {e}")
            raise
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to format data for CSV: {e}")
            raise
    
    def save_phone_specifications(self, phones: List[PhoneSpecifications], 
                                base_filename: Optional[str] = None,
                                include_timestamp: bool = True) -> Dict[str, Path]:
        """
        Save phone specifications to both JSON and CSV formats.
        
        Args:
            phones (List[PhoneSpecifications]): List of phone specifications to save
            base_filename (Optional[str]): Base filename without extension
            include_timestamp (bool): Whether to include timestamp in filenames
            
        Returns:
            Dict[str, Path]: Dictionary with 'json' and 'csv' keys containing file paths
            
        Raises:
            ValueError: If phones list is empty
        """
        if not phones:
            raise ValueError("Cannot save empty phone specifications list")
        
        # Convert phone specifications to dictionaries
        data = [phone.to_dict() for phone in phones]
        
        # Determine base filename
        if base_filename is None:
            base_filename = "phones_data"
        
        # Generate filenames
        json_filename = self.generate_filename(base_filename, 'json', include_timestamp)
        csv_filename = self.generate_filename(base_filename, 'csv', include_timestamp)
        
        # Save to both formats
        json_path = self.save_to_json(data, json_filename, include_timestamp=False)
        csv_path = self.save_to_csv(data, csv_filename, include_timestamp=False)
        
        logger.info(f"Successfully saved {len(phones)} phone specifications to both formats")
        
        return {
            'json': json_path,
            'csv': csv_path
        }
    
    def _prepare_data_for_json(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare data for JSON serialization.
        
        Args:
            data (List[Dict[str, Any]]): Raw data to prepare
            
        Returns:
            List[Dict[str, Any]]: Data prepared for JSON serialization
        """
        prepared_data = []
        
        for item in data:
            prepared_item = {}
            for key, value in item.items():
                # Handle None values
                if value is None:
                    prepared_item[key] = None
                # Convert all values to strings for consistency
                else:
                    prepared_item[key] = str(value) if not isinstance(value, (str, int, float, bool)) else value
            
            prepared_data.append(prepared_item)
        
        return prepared_data
    
    def _get_csv_fieldnames(self, data: List[Dict[str, Any]]) -> List[str]:
        """
        Get all unique field names from data for CSV headers.
        
        Args:
            data (List[Dict[str, Any]]): Data to analyze
            
        Returns:
            List[str]: Sorted list of unique field names
        """
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        
        # Sort fieldnames for consistent column order
        # Put common fields first, then alphabetical order
        priority_fields = ['brand', 'model', 'device_type', 'release_date', 'status']
        sorted_fields = []
        
        # Add priority fields first if they exist
        for field in priority_fields:
            if field in fieldnames:
                sorted_fields.append(field)
                fieldnames.remove(field)
        
        # Add remaining fields in alphabetical order
        sorted_fields.extend(sorted(fieldnames))
        
        return sorted_fields
    
    def _prepare_row_for_csv(self, row: Dict[str, Any], fieldnames: List[str]) -> Dict[str, str]:
        """
        Prepare a data row for CSV writing.
        
        Args:
            row (Dict[str, Any]): Raw data row
            fieldnames (List[str]): Expected field names
            
        Returns:
            Dict[str, str]: Row prepared for CSV writing
        """
        prepared_row = {}
        
        for field in fieldnames:
            value = row.get(field)
            
            # Handle None values
            if value is None:
                prepared_row[field] = ''
            # Handle boolean values
            elif isinstance(value, bool):
                prepared_row[field] = 'Yes' if value else 'No'
            # Convert everything else to string
            else:
                prepared_row[field] = str(value)
        
        return prepared_row
    
    def list_output_files(self, pattern: Optional[str] = None) -> List[Path]:
        """
        List files in the output directory.
        
        Args:
            pattern (Optional[str]): Glob pattern to filter files
            
        Returns:
            List[Path]: List of file paths in output directory
        """
        if not self.output_dir.exists():
            return []
        
        if pattern:
            return list(self.output_dir.glob(pattern))
        else:
            return [f for f in self.output_dir.iterdir() if f.is_file()]
    
    def cleanup_old_files(self, keep_count: int = 5, pattern: str = "*.json") -> int:
        """
        Clean up old files, keeping only the most recent ones.
        
        Args:
            keep_count (int): Number of recent files to keep
            pattern (str): Glob pattern for files to clean up
            
        Returns:
            int: Number of files deleted
        """
        files = self.list_output_files(pattern)
        
        if len(files) <= keep_count:
            return 0
        
        # Sort by modification time (newest first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Delete older files
        files_to_delete = files[keep_count:]
        deleted_count = 0
        
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"Deleted old file: {file_path}")
            except OSError as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
        
        return deleted_count