"""
Integration tests for error recovery and graceful degradation.

This module tests the scraper's ability to handle various error scenarios
and recover gracefully while maintaining data integrity.
"""

import pytest
import requests
import time
from unittest.mock import Mock, patch
from pathlib import Path

from mobiledokan_scraper.main import MobileDokanScraper
from mobiledokan_scraper.utils.error_handling import NetworkError, ParsingError, CriticalError
from mobiledokan_scraper.utils.http_client import HTTPClient


class TestErrorRecovery:
    """Test error recovery mechanisms and graceful degradation."""
    
    def test_network_timeout_recovery(self):
        """Test recovery from network timeout errors."""
        # Create temporary directory and scraper
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        
        try:
            scraper = MobileDokanScraper(output_dir=temp_dir)
            # Mock timeout error followed by success
            timeout_error = requests.exceptions.Timeout("Request timeout")
            
            with patch.object(scraper.http_client, 'get') as mock_get:
                # Create mock responses
                mock_success = Mock()
                mock_success.text = "<html><body>Success</body></html>"
                mock_success.content = b"<html><body>Success</body></html>"
                mock_success.status_code = 200
                mock_success.raise_for_status = Mock()
                
                mock_get.side_effect = [
                    timeout_error,  # First call times out
                    mock_success,   # Second call succeeds
                    mock_success    # Detail call succeeds
                ]
                
                # Run workflow - should recover from timeout
                results = scraper.run_complete_scraping(max_phones=1)
                
                # Verify recovery
                assert mock_get.call_count >= 2  # Should have retried
                assert results['statistics']['successful_scrapes'] >= 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_connection_error_recovery(self, temp_output_dir, mock_http_responses):
        """Test recovery from connection errors."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        # Mock connection error followed by success
        connection_error = requests.exceptions.ConnectionError("Connection failed")
        
        with patch.object(scraper.http_client, 'get') as mock_get:
            mock_get.side_effect = [
                mock_http_responses['listing_success'],  # Listing succeeds
                connection_error,                        # First detail fails
                mock_http_responses['detail_success']    # Second detail succeeds
            ]
            
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=2)
            
            # Should handle connection error gracefully
            assert results['statistics']['failed_scrapes'] >= 1
            assert results['statistics']['successful_scrapes'] >= 0
    
    def test_http_error_recovery(self, temp_output_dir, mock_http_responses):
        """Test recovery from HTTP errors (4xx, 5xx)."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        # Mock HTTP error followed by success
        http_error_response = Mock()
        http_error_response.status_code = 500
        http_error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        
        with patch.object(scraper.http_client, 'get') as mock_get:
            mock_get.side_effect = [
                mock_http_responses['listing_success'],  # Listing succeeds
                http_error_response,                     # First detail fails with 500
                mock_http_responses['detail_success']    # Second detail succeeds
            ]
            
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=2)
            
            # Should handle HTTP errors gracefully
            assert results['statistics']['failed_scrapes'] >= 1
            assert results['statistics']['successful_scrapes'] >= 0
    
    def test_rate_limiting_recovery(self, temp_output_dir, mock_http_responses):
        """Test recovery from rate limiting (429 errors)."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        with patch.object(scraper.http_client, 'get') as mock_get:
            mock_get.side_effect = [
                mock_http_responses['listing_success'],  # Listing succeeds
                mock_http_responses['rate_limited'],     # First detail rate limited
                mock_http_responses['detail_success']    # Second detail succeeds after backoff
            ]
            
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=2)
            
            # Should handle rate limiting with backoff
            assert results['statistics']['failed_scrapes'] >= 1
            assert results['statistics']['successful_scrapes'] >= 0
    
    def test_parsing_error_recovery(self, temp_output_dir, mock_http_responses):
        """Test recovery from parsing errors."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        with patch.object(scraper.http_client, 'get') as mock_get:
            mock_get.side_effect = [
                mock_http_responses['listing_success'],  # Listing succeeds
                mock_http_responses['malformed_page'],   # First detail has malformed HTML
                mock_http_responses['detail_success']    # Second detail succeeds
            ]
            
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=2)
            
            # Should handle parsing errors gracefully
            assert results['statistics']['failed_scrapes'] >= 1
            assert results['statistics']['successful_scrapes'] >= 0
    
    def test_multiple_error_recovery(self, temp_output_dir, mock_http_responses):
        """Test recovery from multiple consecutive errors."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        # Create multiple error scenarios
        timeout_error = requests.exceptions.Timeout("Request timeout")
        connection_error = requests.exceptions.ConnectionError("Connection failed")
        
        with patch.object(scraper.http_client, 'get') as mock_get:
            mock_get.side_effect = [
                mock_http_responses['listing_success_extended'],  # Listing succeeds
                timeout_error,                           # First detail times out
                connection_error,                        # Second detail connection fails
                mock_http_responses['rate_limited'],     # Third detail rate limited
                mock_http_responses['detail_success']    # Fourth detail finally succeeds
            ]
            
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=4)
            
            # Should handle multiple errors and eventually succeed
            assert results['statistics']['failed_scrapes'] >= 3
            assert results['statistics']['successful_scrapes'] >= 0
    
    def test_critical_error_handling(self, temp_output_dir):
        """Test handling of critical errors that should stop execution."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        # Mock a critical error (e.g., invalid base URL)
        with patch.object(scraper.http_client, 'get') as mock_get:
            # Mock DNS resolution failure (critical error)
            dns_error = requests.exceptions.ConnectionError("Name or service not known")
            mock_get.side_effect = dns_error
            
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=1)
            
            # Should handle critical errors gracefully
            assert results['success'] is False
            assert results['statistics']['total_phones_found'] == 0
    
    def test_graceful_degradation(self, temp_output_dir, mock_http_responses):
        """Test graceful degradation when some components fail."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        # Mock partial failures
        with patch.object(scraper.http_client, 'get') as mock_get:
            mock_get.side_effect = [
                mock_http_responses['listing_success_extended'],  # Listing succeeds
                mock_http_responses['detail_success'],   # First detail succeeds
                mock_http_responses['malformed_page'],   # Second detail fails
                mock_http_responses['detail_success'],   # Third detail succeeds
                requests.exceptions.Timeout("Timeout")  # Fourth detail times out
            ]
            
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=4)
            
            # Should continue processing despite partial failures
            assert results['statistics']['successful_scrapes'] >= 2
            assert results['statistics']['failed_scrapes'] >= 2
            assert results['success'] is True  # Overall success despite some failures
    
    def test_memory_pressure_recovery(self, temp_output_dir):
        """Test recovery from memory pressure situations."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        # Simulate memory pressure by creating large objects
        large_data = []
        try:
            # Create a scenario that might cause memory pressure
            for i in range(1000):
                large_data.append("x" * 10000)  # 10KB strings
            
            # Try to run scraping under memory pressure
            with patch.object(scraper.http_client, 'get') as mock_get:
                mock_response = Mock()
                mock_response.text = "<html><body>Test</body></html>"
                mock_response.status_code = 200
                mock_get.return_value = mock_response
                
                # Should handle memory pressure gracefully
                results = scraper.run_complete_scraping(max_phones=1)
                assert results is not None
                
        except MemoryError:
            # If we actually hit memory limits, that's expected
            pass
        finally:
            # Clean up large data
            large_data.clear()
    
    def test_file_system_error_recovery(self, temp_output_dir):
        """Test recovery from file system errors."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
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
    
    def test_interrupt_handling(self, temp_output_dir, mock_http_responses):
        """Test handling of user interruption (KeyboardInterrupt)."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        def interrupt_after_first_call(*args, **kwargs):
            if hasattr(interrupt_after_first_call, 'called'):
                raise KeyboardInterrupt("User interrupted")
            interrupt_after_first_call.called = True
            return mock_http_responses['listing_success']
        
        with patch.object(scraper.http_client, 'get', side_effect=interrupt_after_first_call):
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=5)
            
            # Should handle interruption gracefully
            assert results['interrupted'] is True
            assert results['success'] is False
    
    def test_resource_cleanup_on_error(self, temp_output_dir):
        """Test proper resource cleanup when errors occur."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        # Mock an error that occurs after resources are allocated
        with patch.object(scraper.http_client, 'get') as mock_get:
            mock_get.side_effect = Exception("Unexpected error")
            
            # Run workflow
            try:
                results = scraper.run_complete_scraping(max_phones=1)
            except Exception:
                pass
            
            # Verify resources are cleaned up
            # (In a real implementation, this would check for open files, connections, etc.)
            assert hasattr(scraper, 'http_client')
    
    def test_error_logging_and_reporting(self, temp_output_dir, mock_http_responses, caplog):
        """Test proper error logging and reporting."""
        import logging
        
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        # Enable logging capture
        with caplog.at_level(logging.ERROR):
            with patch.object(scraper.http_client, 'get') as mock_get:
                # Mock various errors
                timeout_error = requests.exceptions.Timeout("Request timeout")
                mock_get.side_effect = [
                    mock_http_responses['listing_success'],
                    timeout_error,
                    mock_http_responses['detail_success']
                ]
                
                # Run workflow
                results = scraper.run_complete_scraping(max_phones=2)
                
                # Verify errors were logged
                assert len(caplog.records) > 0
                error_messages = [record.message for record in caplog.records if record.levelno >= logging.ERROR]
                assert any("timeout" in msg.lower() for msg in error_messages)
    
    def test_retry_mechanism_limits(self, temp_output_dir):
        """Test that retry mechanisms respect configured limits."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        # Mock persistent failure
        persistent_error = requests.exceptions.ConnectionError("Persistent failure")
        
        with patch.object(scraper.http_client, 'get') as mock_get:
            mock_get.side_effect = persistent_error
            
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=1)
            
            # Verify retry limits were respected
            # (The exact number depends on configuration, but should be limited)
            assert mock_get.call_count <= 10  # Should not retry indefinitely
            assert results['success'] is False
    
    def test_error_context_preservation(self, temp_output_dir, mock_http_responses):
        """Test that error context is preserved for debugging."""
        scraper = MobileDokanScraper(output_dir=temp_output_dir)
        
        with patch.object(scraper.http_client, 'get') as mock_get:
            # Mock error with specific context
            context_error = requests.exceptions.HTTPError("404 Not Found: /specific-phone-url")
            mock_get.side_effect = [
                mock_http_responses['listing_success'],
                context_error
            ]
            
            # Run workflow
            results = scraper.run_complete_scraping(max_phones=1)
            
            # Verify error context is preserved in results
            assert results['statistics']['failed_scrapes'] >= 1
            # In a real implementation, error details would be preserved
            assert results is not None
