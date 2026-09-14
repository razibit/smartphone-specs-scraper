"""
Tests for error handling and logging functionality.

This module tests the comprehensive error handling system including
custom exceptions, error recovery, graceful degradation, and logging integration.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, RequestException

from mobiledokan_scraper.utils.error_handling import (
    ScraperError,
    NetworkError,
    ParsingError,
    ValidationError,
    CriticalError,
    ErrorRecovery,
    GracefulDegradation,
    retry_on_error,
    handle_network_error,
    handle_parsing_error,
    setup_error_handling
)
from mobiledokan_scraper.utils.logging_config import ScraperLogger


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_scraper_error_creation(self):
        """Test ScraperError creation with context."""
        context = {"url": "http://example.com", "attempt": 1}
        error = ScraperError("Test error", "test", context)
        
        assert str(error) == "Test error"
        assert error.error_type == "test"
        assert error.context == context
        assert error.timestamp > 0
    
    def test_network_error_creation(self):
        """Test NetworkError creation with URL and status code."""
        error = NetworkError("Connection failed", "http://example.com", 404)
        
        assert str(error) == "Connection failed"
        assert error.error_type == "network"
        assert error.url == "http://example.com"
        assert error.status_code == 404
    
    def test_parsing_error_creation(self):
        """Test ParsingError creation with element info."""
        error = ParsingError("Failed to parse", "http://example.com", "title")
        
        assert str(error) == "Failed to parse"
        assert error.error_type == "parsing"
        assert error.url == "http://example.com"
        assert error.element == "title"
    
    def test_validation_error_creation(self):
        """Test ValidationError creation with field info."""
        error = ValidationError("Invalid value", "price", "invalid")
        
        assert str(error) == "Invalid value"
        assert error.error_type == "validation"
        assert error.field == "price"
        assert error.value == "invalid"
    
    def test_critical_error_creation(self):
        """Test CriticalError creation."""
        error = CriticalError("System failure")
        
        assert str(error) == "System failure"
        assert error.error_type == "critical"


class TestErrorRecovery:
    """Test error recovery functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = Mock(spec=ScraperLogger)
        self.error_recovery = ErrorRecovery(self.mock_logger)
    
    def test_network_error_recovery_404(self):
        """Test recovery from 404 network errors."""
        error = NetworkError("Not found", "http://example.com", 404)
        
        result = self.error_recovery.recover_from_error(error)
        
        assert result is True
        self.mock_logger.log_error.assert_called_once()
    
    def test_network_error_recovery_429(self):
        """Test recovery from rate limiting errors."""
        error = NetworkError("Rate limited", "http://example.com", 429)
        
        with patch('time.sleep') as mock_sleep:
            result = self.error_recovery.recover_from_error(error)
        
        assert result is True
        mock_sleep.assert_called_once_with(30)
    
    def test_parsing_error_recovery(self):
        """Test recovery from parsing errors."""
        error = ParsingError("Failed to parse", element="title")
        
        result = self.error_recovery.recover_from_error(error)
        
        assert result is True
        self.mock_logger.log_error.assert_called_once()
    
    def test_critical_error_no_recovery(self):
        """Test that critical errors cannot be recovered from."""
        error = CriticalError("System failure")
        
        result = self.error_recovery.recover_from_error(error)
        
        assert result is False
        self.mock_logger.log_error.assert_called_once()


class TestGracefulDegradation:
    """Test graceful degradation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.graceful_degradation = GracefulDegradation()
    
    def test_get_safe_value_with_valid_data(self):
        """Test getting safe value with valid data."""
        result = self.graceful_degradation.get_safe_value("brand", "Samsung")
        assert result == "Samsung"
    
    def test_get_safe_value_with_none(self):
        """Test getting safe value with None."""
        result = self.graceful_degradation.get_safe_value("brand", None)
        assert result == "Unknown"
    
    def test_get_safe_value_with_empty_string(self):
        """Test getting safe value with empty string."""
        result = self.graceful_degradation.get_safe_value("brand", "")
        assert result == "Unknown"
    
    def test_get_safe_value_with_fallback(self):
        """Test getting safe value with custom fallback."""
        result = self.graceful_degradation.get_safe_value("brand", None, "N/A")
        assert result == "N/A"
    
    def test_extract_with_fallback_success(self):
        """Test successful HTML extraction."""
        html = "<div class='title'>Test Phone</div>"
        soup = BeautifulSoup(html, 'html.parser')
        
        result = self.graceful_degradation.extract_with_fallback(soup, ".title")
        assert result == "Test Phone"
    
    def test_extract_with_fallback_missing_element(self):
        """Test HTML extraction with missing element."""
        html = "<div>No title here</div>"
        soup = BeautifulSoup(html, 'html.parser')
        
        result = self.graceful_degradation.extract_with_fallback(soup, ".title", default="Not Found")
        assert result == "Not Found"
    
    def test_safe_json_extract_success(self):
        """Test successful JSON extraction."""
        data = {"user": {"profile": {"name": "John Doe"}}}
        
        result = self.graceful_degradation.safe_json_extract(data, "user.profile.name")
        assert result == "John Doe"
    
    def test_safe_json_extract_missing_key(self):
        """Test JSON extraction with missing key."""
        data = {"user": {"profile": {}}}
        
        result = self.graceful_degradation.safe_json_extract(data, "user.profile.name", "Unknown")
        assert result == "Unknown"


class TestDecorators:
    """Test error handling decorators."""
    
    def test_retry_on_error_success(self):
        """Test retry decorator with successful function."""
        @retry_on_error(max_retries=2)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_retry_on_error_with_retries(self):
        """Test retry decorator with function that fails then succeeds."""
        call_count = 0
        
        @retry_on_error(max_retries=2, backoff_factor=0.1)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return "success"
        
        with patch('time.sleep'):
            result = failing_then_success()
        
        assert result == "success"
        assert call_count == 2
    
    def test_handle_network_error_success(self):
        """Test network error handler with successful function."""
        @handle_network_error
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_handle_network_error_with_error(self):
        """Test network error handler with failing function."""
        @handle_network_error
        def failing_function():
            raise ConnectionError("Connection failed")
        
        result = failing_function()
        assert result is None
    
    def test_handle_parsing_error_with_default(self):
        """Test parsing error handler with default value."""
        @handle_parsing_error
        def failing_function():
            raise ValueError("Parsing failed")
        
        result = failing_function()
        assert result is None


class TestSetupFunctions:
    """Test setup and utility functions."""
    
    def test_setup_error_handling(self):
        """Test error handling setup function."""
        mock_logger = Mock(spec=ScraperLogger)
        
        error_recovery, graceful_degradation = setup_error_handling(mock_logger)
        
        assert isinstance(error_recovery, ErrorRecovery)
        assert isinstance(graceful_degradation, GracefulDegradation)
        assert error_recovery.logger == mock_logger


if __name__ == "__main__":
    pytest.main([__file__])