"""
Unit tests for the HTTP client module.

Tests cover error handling, rate limiting, retry logic, and various
HTTP scenarios that the scraper might encounter.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import requests
from requests.exceptions import (
    ConnectionError, 
    Timeout, 
    HTTPError, 
    TooManyRedirects,
    RequestException
)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mobiledokan_scraper.utils.http_client import HTTPClient
from mobiledokan_scraper.config.settings import (
    USER_AGENTS, 
    REQUEST_DELAY, 
    MAX_RETRIES,
    BACKOFF_FACTOR,
    INITIAL_BACKOFF
)


class TestHTTPClient(unittest.TestCase):
    """Test cases for HTTPClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = HTTPClient(delay=0.1, timeout=5)  # Shorter delays for testing
        
    def tearDown(self):
        """Clean up after tests."""
        self.client.close()
    
    def test_initialization(self):
        """Test HTTPClient initialization."""
        client = HTTPClient(delay=2.0, timeout=10)
        self.assertEqual(client.delay, 2.0)
        self.assertEqual(client.timeout, 10)
        self.assertIsNotNone(client.session)
        client.close()
    
    def test_default_initialization(self):
        """Test HTTPClient initialization with default values."""
        client = HTTPClient()
        self.assertEqual(client.delay, REQUEST_DELAY)
        self.assertEqual(client.timeout, 30)  # Default timeout
        client.close()
    
    def test_get_random_user_agent(self):
        """Test user agent rotation."""
        user_agent = self.client._get_random_user_agent()
        self.assertIn(user_agent, USER_AGENTS)
        
        # Test that we get different user agents (run multiple times)
        user_agents = set()
        for _ in range(20):
            user_agents.add(self.client._get_random_user_agent())
        
        # Should get at least 2 different user agents in 20 tries
        self.assertGreater(len(user_agents), 1)
    
    def test_prepare_headers(self):
        """Test header preparation."""
        headers = self.client._prepare_headers()
        self.assertIn('User-Agent', headers)
        self.assertIn(headers['User-Agent'], USER_AGENTS)
        
        # Test with additional headers
        additional = {'Custom-Header': 'test-value'}
        headers = self.client._prepare_headers(additional)
        self.assertIn('User-Agent', headers)
        self.assertIn('Custom-Header', headers)
        self.assertEqual(headers['Custom-Header'], 'test-value')
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        start_time = time.time()
        
        # First call should not delay
        self.client._enforce_rate_limit()
        first_call_time = time.time() - start_time
        self.assertLess(first_call_time, 0.05)  # Should be very quick
        
        # Second call should delay
        start_time = time.time()
        self.client._enforce_rate_limit()
        second_call_time = time.time() - start_time
        self.assertGreaterEqual(second_call_time, self.client.delay * 0.9)  # Allow some tolerance
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    def test_successful_get_request(self, mock_get):
        """Test successful GET request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        response = self.client.get('http://example.com')
        
        self.assertEqual(response, mock_response)
        mock_get.assert_called_once()
        
        # Check that headers were set
        call_args = mock_get.call_args
        self.assertIn('headers', call_args.kwargs)
        self.assertIn('User-Agent', call_args.kwargs['headers'])
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    def test_404_error_no_retry(self, mock_get):
        """Test that 404 errors are not retried."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = HTTPError()
        http_error.response = mock_response
        mock_get.side_effect = http_error
        
        with self.assertRaises(HTTPError):
            self.client.get('http://example.com/notfound')
        
        # Should only be called once (no retries for 404)
        self.assertEqual(mock_get.call_count, 1)
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    @patch('time.sleep')
    def test_rate_limit_retry(self, mock_sleep, mock_get):
        """Test retry logic for rate limiting (429 errors)."""
        # Mock 429 response then success
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        http_error = HTTPError()
        http_error.response = mock_response_429
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status.return_value = None
        
        mock_get.side_effect = [http_error, mock_response_success]
        
        response = self.client.get('http://example.com')
        
        self.assertEqual(response, mock_response_success)
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once()  # Should have slept for backoff
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    @patch('time.sleep')
    def test_server_error_retry(self, mock_sleep, mock_get):
        """Test retry logic for server errors (5xx)."""
        # Mock 500 response then success
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        http_error = HTTPError()
        http_error.response = mock_response_500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status.return_value = None
        
        mock_get.side_effect = [http_error, mock_response_success]
        
        response = self.client.get('http://example.com')
        
        self.assertEqual(response, mock_response_success)
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once()
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    @patch('time.sleep')
    def test_connection_error_retry(self, mock_sleep, mock_get):
        """Test retry logic for connection errors."""
        # Mock connection error then success
        connection_error = ConnectionError("Connection failed")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status.return_value = None
        
        mock_get.side_effect = [connection_error, mock_response_success]
        
        response = self.client.get('http://example.com')
        
        self.assertEqual(response, mock_response_success)
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once()
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    @patch('time.sleep')
    def test_timeout_retry(self, mock_sleep, mock_get):
        """Test retry logic for timeout errors."""
        # Mock timeout then success
        timeout_error = Timeout("Request timed out")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status.return_value = None
        
        mock_get.side_effect = [timeout_error, mock_response_success]
        
        response = self.client.get('http://example.com')
        
        self.assertEqual(response, mock_response_success)
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once()
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    def test_too_many_redirects_no_retry(self, mock_get):
        """Test that redirect loops are not retried."""
        redirect_error = TooManyRedirects("Too many redirects")
        mock_get.side_effect = redirect_error
        
        with self.assertRaises(TooManyRedirects):
            self.client.get('http://example.com')
        
        # Should only be called once (no retries for redirect loops)
        self.assertEqual(mock_get.call_count, 1)
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    @patch('time.sleep')
    def test_max_retries_exceeded(self, mock_sleep, mock_get):
        """Test behavior when max retries are exceeded."""
        # Mock connection error for all attempts
        connection_error = ConnectionError("Connection failed")
        mock_get.side_effect = connection_error
        
        with self.assertRaises(ConnectionError):
            self.client.get('http://example.com', retries=2)
        
        # Should be called 3 times (initial + 2 retries)
        self.assertEqual(mock_get.call_count, 3)
        # Should sleep 3 times (rate limiting + 2 retries)
        self.assertEqual(mock_sleep.call_count, 3)
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    @patch('time.sleep')
    def test_exponential_backoff(self, mock_sleep, mock_get):
        """Test exponential backoff timing."""
        # Mock connection errors
        connection_error = ConnectionError("Connection failed")
        mock_get.side_effect = connection_error
        
        with self.assertRaises(ConnectionError):
            self.client.get('http://example.com', retries=2)
        
        # Check that sleep was called with increasing delays
        sleep_calls = mock_sleep.call_args_list
        self.assertEqual(len(sleep_calls), 3)  # Rate limiting + 2 retries
        
        # Find the backoff delays (they should be 1, 2, 4 based on exponential backoff)
        backoff_delays = [call[0][0] for call in sleep_calls]
        
        # Should contain INITIAL_BACKOFF and INITIAL_BACKOFF * BACKOFF_FACTOR
        self.assertIn(INITIAL_BACKOFF, backoff_delays)
        self.assertIn(INITIAL_BACKOFF * BACKOFF_FACTOR, backoff_delays)
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    @patch('time.sleep')
    def test_get_with_backoff(self, mock_sleep, mock_get):
        """Test get_with_backoff method."""
        # Mock 429 response then success
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        http_error = HTTPError()
        http_error.response = mock_response_429
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status.return_value = None
        
        mock_get.side_effect = [http_error, mock_response_success]
        
        response = self.client.get_with_backoff('http://example.com')
        
        self.assertEqual(response, mock_response_success)
        self.assertEqual(mock_get.call_count, 2)
        # Should sleep multiple times (rate limiting + backoff + rate limiting again)
        self.assertGreaterEqual(mock_sleep.call_count, 2)
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.head')
    def test_head_request(self, mock_head):
        """Test HEAD request functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_head.return_value = mock_response
        
        response = self.client.head('http://example.com')
        
        self.assertEqual(response, mock_response)
        mock_head.assert_called_once()
        
        # Check that headers were set
        call_args = mock_head.call_args
        self.assertIn('headers', call_args.kwargs)
        self.assertIn('User-Agent', call_args.kwargs['headers'])
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with HTTPClient() as client:
            self.assertIsNotNone(client.session)
        
        # Session should be closed after context exit
        # Note: We can't easily test this without accessing private attributes
    
    def test_get_session_info(self):
        """Test session info retrieval."""
        info = self.client.get_session_info()
        
        self.assertIn('delay', info)
        self.assertIn('timeout', info)
        self.assertIn('user_agents_count', info)
        self.assertIn('max_retries', info)
        self.assertIn('backoff_factor', info)
        self.assertIn('verify_certificates', info)
        
        self.assertEqual(info['delay'], self.client.delay)
        self.assertEqual(info['timeout'], self.client.timeout)
        self.assertEqual(info['user_agents_count'], len(USER_AGENTS))
        self.assertEqual(info['max_retries'], MAX_RETRIES)
        self.assertEqual(info['backoff_factor'], BACKOFF_FACTOR)
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    def test_custom_headers_preserved(self, mock_get):
        """Test that custom headers are preserved in requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        custom_headers = {'Authorization': 'Bearer token123'}
        self.client.get('http://example.com', headers=custom_headers)
        
        call_args = mock_get.call_args
        headers = call_args.kwargs['headers']
        
        self.assertIn('User-Agent', headers)
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['Authorization'], 'Bearer token123')
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    def test_timeout_parameter(self, mock_get):
        """Test that timeout parameter is passed correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        self.client.get('http://example.com', timeout=15)
        
        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs['timeout'], 15)
    
    @patch('mobiledokan_scraper.utils.http_client.requests.Session.get')
    def test_verify_parameter(self, mock_get):
        """Test that SSL verification parameter is passed correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        self.client.get('http://example.com', verify=False)
        
        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs['verify'], False)


if __name__ == '__main__':
    unittest.main()