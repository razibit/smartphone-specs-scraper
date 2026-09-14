"""
Simple integration tests to verify basic functionality.
"""

import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch

from smartphone_specs_scraper.main import MobileDokanScraper


class TestSimpleIntegration:
    """Simple integration tests without complex fixtures."""
    
    def test_scraper_initialization(self):
        """Test that the scraper can be initialized properly."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            assert scraper is not None
            assert hasattr(scraper, 'http_client')
            assert hasattr(scraper, 'listing_scraper')
            assert hasattr(scraper, 'detail_scraper')
            assert hasattr(scraper, 'file_manager')
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_results_summary_creation(self):
        """Test that results summary is created correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            
            # Test creating a results summary
            results = scraper._create_results_summary(
                success=True,
                phone_specifications=[],
                export_results={'success': True, 'files': {}, 'record_count': 0}
            )
            
            assert results['success'] is True
            assert 'statistics' in results
            assert 'scraped_data' in results
            assert 'export_results' in results
            assert 'timestamp' in results
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @patch('smartphone_specs_scraper.utils.http_client.HTTPClient.get')
    def test_error_handling_in_workflow(self, mock_get):
        """Test that errors in workflow are handled gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            
            # Mock a network error
            import requests
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            # Run workflow - should handle error gracefully
            results = scraper.run_complete_scraping(max_phones=1)
            
            # Should not crash and should return results
            assert results is not None
            assert 'success' in results
            assert 'statistics' in results
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)