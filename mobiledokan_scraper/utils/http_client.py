"""
HTTP client with error handling, rate limiting, and retry logic.

This module provides a robust HTTP client specifically designed for web scraping
with proper error handling, rate limiting, and respectful request patterns.
"""

import time
import random
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import (
    RequestException, 
    ConnectionError, 
    Timeout, 
    HTTPError,
    TooManyRedirects
)
from urllib3.util.retry import Retry

from ..config.settings import (
    USER_AGENTS,
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    BACKOFF_FACTOR,
    INITIAL_BACKOFF,
    VERIFY_CERTIFICATES
)
from .error_handling import NetworkError, retry_on_error


class HTTPClient:
    """
    HTTP client with built-in error handling, rate limiting, and retry logic.
    
    Features:
    - User-Agent rotation
    - Request delays to be respectful to servers
    - Exponential backoff for failed requests
    - Comprehensive error handling
    - Connection pooling and session management
    """
    
    def __init__(self, delay: float = REQUEST_DELAY, timeout: int = REQUEST_TIMEOUT):
        """
        Initialize the HTTP client.
        
        Args:
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
        """
        self.delay = delay
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Initialize session with connection pooling
        self.session = requests.Session()
        
        # Configure retry strategy for the session
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.last_request_time = 0
        
    def _get_random_user_agent(self) -> str:
        """Get a random User-Agent string from the configured list."""
        return random.choice(USER_AGENTS)
    
    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by adding delays between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.delay:
            sleep_time = self.delay - time_since_last_request
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _prepare_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Prepare headers for the request including User-Agent rotation.
        
        Args:
            additional_headers: Optional additional headers to include
            
        Returns:
            Dictionary of headers to use for the request
        """
        headers = {
            'User-Agent': self._get_random_user_agent()
        }
        
        if additional_headers:
            headers.update(additional_headers)
            
        return headers
    
    def get(self, url: str, retries: int = MAX_RETRIES, **kwargs) -> requests.Response:
        """
        Perform a GET request with error handling and retry logic.
        
        Args:
            url: URL to request
            retries: Number of retry attempts (defaults to MAX_RETRIES)
            **kwargs: Additional arguments to pass to requests.get()
            
        Returns:
            requests.Response object
            
        Raises:
            RequestException: If all retry attempts fail
        """
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Prepare headers
        headers = self._prepare_headers(kwargs.pop('headers', None))
        
        # Set default timeout if not provided
        timeout = kwargs.pop('timeout', self.timeout)
        
        # Set SSL verification
        verify = kwargs.pop('verify', VERIFY_CERTIFICATES)
        
        attempt = 0
        last_exception = None
        
        while attempt <= retries:
            try:
                self.logger.debug(f"Attempting request to {url} (attempt {attempt + 1}/{retries + 1})")
                
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    verify=verify,
                    **kwargs
                )
                
                # Raise an exception for bad status codes
                response.raise_for_status()
                
                self.logger.debug(f"Successfully retrieved {url} (status: {response.status_code})")
                return response
                
            except HTTPError as e:
                last_exception = e
                status_code = e.response.status_code if e.response else None
                
                if status_code == 404:
                    self.logger.warning(f"Page not found (404): {url}")
                    raise e  # Don't retry 404 errors
                elif status_code == 429:
                    # Rate limited - use exponential backoff
                    backoff_time = INITIAL_BACKOFF * (BACKOFF_FACTOR ** attempt)
                    self.logger.warning(f"Rate limited (429). Backing off for {backoff_time} seconds")
                    time.sleep(backoff_time)
                elif 500 <= status_code < 600:
                    # Server error - retry with backoff
                    backoff_time = INITIAL_BACKOFF * (BACKOFF_FACTOR ** attempt)
                    self.logger.warning(f"Server error ({status_code}). Retrying in {backoff_time} seconds")
                    time.sleep(backoff_time)
                else:
                    self.logger.error(f"HTTP error {status_code} for {url}: {e}")
                    raise e  # Don't retry other HTTP errors
                    
            except (ConnectionError, Timeout) as e:
                last_exception = e
                backoff_time = INITIAL_BACKOFF * (BACKOFF_FACTOR ** attempt)
                self.logger.warning(f"Connection/timeout error for {url}. Retrying in {backoff_time} seconds: {e}")
                time.sleep(backoff_time)
                
            except TooManyRedirects as e:
                last_exception = e
                self.logger.error(f"Too many redirects for {url}: {e}")
                raise e  # Don't retry redirect loops
                
            except RequestException as e:
                last_exception = e
                self.logger.error(f"Request exception for {url}: {e}")
                if attempt == retries:
                    raise e
                
                backoff_time = INITIAL_BACKOFF * (BACKOFF_FACTOR ** attempt)
                self.logger.warning(f"Retrying in {backoff_time} seconds")
                time.sleep(backoff_time)
            
            attempt += 1
        
        # If we get here, all retries failed
        self.logger.error(f"All {retries + 1} attempts failed for {url}")
        if last_exception:
            raise last_exception
        else:
            raise RequestException(f"Failed to retrieve {url} after {retries + 1} attempts")
    
    def get_with_backoff(self, url: str, max_backoff: int = 60) -> requests.Response:
        """
        Perform a GET request with aggressive exponential backoff for rate limiting.
        
        This method is useful when dealing with strict rate limits and you want
        to be extra respectful to the server.
        
        Args:
            url: URL to request
            max_backoff: Maximum backoff time in seconds
            
        Returns:
            requests.Response object
            
        Raises:
            RequestException: If the request fails after all attempts
        """
        attempt = 0
        
        while attempt <= MAX_RETRIES:
            try:
                return self.get(url, retries=0)  # Don't retry in get(), handle it here
                
            except HTTPError as e:
                if e.response and e.response.status_code == 429:
                    # Calculate exponential backoff with jitter
                    backoff_time = min(
                        INITIAL_BACKOFF * (BACKOFF_FACTOR ** attempt) + random.uniform(0, 1),
                        max_backoff
                    )
                    self.logger.warning(f"Rate limited. Backing off for {backoff_time:.2f} seconds")
                    time.sleep(backoff_time)
                    attempt += 1
                else:
                    raise e
                    
            except (ConnectionError, Timeout) as e:
                backoff_time = min(
                    INITIAL_BACKOFF * (BACKOFF_FACTOR ** attempt),
                    max_backoff
                )
                self.logger.warning(f"Connection error. Backing off for {backoff_time} seconds: {e}")
                time.sleep(backoff_time)
                attempt += 1
                
                if attempt > MAX_RETRIES:
                    raise e
        
        raise RequestException(f"Failed to retrieve {url} after {MAX_RETRIES + 1} attempts with backoff")
    
    def head(self, url: str, **kwargs) -> requests.Response:
        """
        Perform a HEAD request with error handling.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments to pass to requests.head()
            
        Returns:
            requests.Response object
        """
        self._enforce_rate_limit()
        headers = self._prepare_headers(kwargs.pop('headers', None))
        timeout = kwargs.pop('timeout', self.timeout)
        verify = kwargs.pop('verify', VERIFY_CERTIFICATES)
        
        try:
            response = self.session.head(
                url,
                headers=headers,
                timeout=timeout,
                verify=verify,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except RequestException as e:
            self.logger.error(f"HEAD request failed for {url}: {e}")
            raise e
    
    def close(self) -> None:
        """Close the HTTP session and clean up resources."""
        if self.session:
            self.session.close()
            self.logger.debug("HTTP session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.
        
        Returns:
            Dictionary containing session information
        """
        return {
            'delay': self.delay,
            'timeout': self.timeout,
            'user_agents_count': len(USER_AGENTS),
            'max_retries': MAX_RETRIES,
            'backoff_factor': BACKOFF_FACTOR,
            'verify_certificates': VERIFY_CERTIFICATES
        }