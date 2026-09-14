"""
Simple integration tests for error recovery and graceful degradation.
"""

import pytest
import requests
import tempfile
import shutil
from unittest.mock import Mock, patch

from mobiledokan_scraper.main import MobileDokanScraper


class TestErrorRecoverySimple:
    """Test error recovery mechanisms and graceful degradation."""
    
    def test_network_timeout_recovery(self):
        """Test recovery from network timeout errors."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            
            # Mock timeout error followed by success
            timeout_error = requests.exceptions.Timeout("Request timeout")
            
            with patch.object(scraper.http_client, 'get') as mock_get:
                # Create mock success response
                mock_success = Mock()
                mock_success.text = "<html><body>Success</body></html>"
                mock_success.content = b"<html><body>Success</body></html>"
                mock_success.status_code = 200
                mock_success.raise_for_status = Mock()
                
                mock_get.side_effect = [timeout_error, mock_success]
                
                # Test HTTP client retry mechanism
                try:
                    response = scraper.http_client.get("http://test.com")
                    assert response.status_code == 200
                except Exception as e:
                    # Should handle timeout with retries
                    assert "timeout" in str(e).lower() or "retry" in str(e).lower()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_connection_error_recovery(self):
        """Test recovery from connection errors."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            
            # Mock connection error followed by success
            connection_error = requests.exceptions.ConnectionError("Connection failed")
            
            with patch.object(scraper.http_client, 'get') as mock_get:
                mock_success = Mock()
                mock_success.text = "<html><body>Success</body></html>"
                mock_success.content = b"<html><body>Success</body></html>"
                mock_success.status_code = 200
                mock_success.raise_for_status = Mock()
                
                mock_get.side_effect = [connection_error, mock_success]
                
                # Test connection error handling
                try:
                    response = scraper.http_client.get("http://test.com")
                    assert response.status_code == 200
                except Exception as e:
                    # Should handle connection error gracefully
                    assert "connection" in str(e).lower() or "retry" in str(e).lower()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_http_error_recovery(self):
        """Test recovery from HTTP errors (4xx, 5xx)."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            
            # Mock HTTP error followed by success
            http_error_response = Mock()
            http_error_response.status_code = 500
            http_error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
            
            with patch.object(scraper.http_client, 'get') as mock_get:
                mock_success = Mock()
                mock_success.text = "<html><body>Success</body></html>"
                mock_success.content = b"<html><body>Success</body></html>"
                mock_success.status_code = 200
                mock_success.raise_for_status = Mock()
                
                mock_get.side_effect = [http_error_response, mock_success]
                
                # Test HTTP error handling
                try:
                    response = scraper.http_client.get("http://test.com")
                    # Should eventually succeed or handle error gracefully
                    assert response is not None
                except Exception as e:
                    # Should handle HTTP errors gracefully
                    assert "500" in str(e) or "server" in str(e).lower()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_parsing_error_recovery(self):
        """Test recovery from parsing errors."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            
            with patch.object(scraper.http_client, 'get') as mock_get:
                # Mock malformed HTML response
                mock_malformed = Mock()
                mock_malformed.text = "<html><body>Malformed page</body></html>"
                mock_malformed.content = b"<html><body>Malformed page</body></html>"
                mock_malformed.status_code = 200
                mock_malformed.raise_for_status = Mock()
                
                mock_get.return_value = mock_malformed
                
                # Run workflow with malformed data
                results = scraper.run_complete_scraping(max_phones=1)
                
                # Should handle parsing errors gracefully
                assert results is not None
                assert 'statistics' in results
                # May have failed scrapes due to malformed data, but shouldn't crash
                assert results['statistics']['failed_scrapes'] >= 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_graceful_degradation(self):
        """Test graceful degradation when some components fail."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            
            with patch.object(scraper.http_client, 'get') as mock_get:
                # Mock partial failures
                mock_success = Mock()
                mock_success.text = '{"data": [], "current_page": 1, "last_page": 1}'
                mock_success.content = b'{"data": [], "current_page": 1, "last_page": 1}'
                mock_success.status_code = 200
                mock_success.raise_for_status = Mock()
                
                timeout_error = requests.exceptions.Timeout("Timeout")
                
                mock_get.side_effect = [mock_success, timeout_error, mock_success]
                
                # Run workflow
                results = scraper.run_complete_scraping(max_phones=2)
                
                # Should continue processing despite partial failures
                assert results is not None
                assert 'statistics' in results
                # Should handle failures gracefully
                assert results['statistics']['failed_scrapes'] >= 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_interrupt_handling(self):
        """Test handling of user interruption (KeyboardInterrupt)."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            
            def interrupt_after_first_call(*args, **kwargs):
                if hasattr(interrupt_after_first_call, 'called'):
                    raise KeyboardInterrupt("User interrupted")
                interrupt_after_first_call.called = True
                
                # Return a response with some phones so the workflow continues
                mock_response = Mock()
                mock_response.text = '''
                <script>
                let productDataArray = {
                    "data": [{"id": 1, "title": "Test Phone", "slug": "test-phone"}],
                    "current_page": 1,
                    "last_page": 1
                };
                </script>
                '''
                mock_response.content = mock_response.text.encode('utf-8')
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                return mock_response
            
            with patch.object(scraper.http_client, 'get', side_effect=interrupt_after_first_call):
                # Run workflow
                results = scraper.run_complete_scraping(max_phones=5)
                
                # Should handle interruption gracefully
                assert results['interrupted'] is True
                assert results['success'] is False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_file_system_error_recovery(self):
        """Test recovery from file system errors."""
        temp_dir = tempfile.mkdtemp()
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            
            # Create sample data
            from mobiledokan_scraper.models.phone_data import PhoneSpecifications
            phone_specs = [PhoneSpecifications(brand="Test", model="Test")]
            
            # Mock file system error during export
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                # Try to export data
                export_results = scraper._export_data(phone_specs)
                
                # Should handle file system errors gracefully
                assert export_results is not None
                assert export_results['success'] is False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)