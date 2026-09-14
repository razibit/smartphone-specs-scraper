"""
Comprehensive error handling utilities for MobileDokan scraper.

This module provides custom exceptions, error recovery mechanisms,
and graceful degradation strategies for various error scenarios.
"""

import time
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, Union
from functools import wraps
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError
from bs4 import BeautifulSoup

from .logging_config import ScraperLogger

T = TypeVar('T')


class ScraperError(Exception):
    """Base exception class for scraper-related errors."""
    
    def __init__(self, message: str, error_type: str = "general", 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_type = error_type
        self.context = context or {}
        self.timestamp = time.time()


class NetworkError(ScraperError):
    """Exception for network-related errors."""
    
    def __init__(self, message: str, url: str = "", status_code: Optional[int] = None,
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "network", context)
        self.url = url
        self.status_code = status_code


class ParsingError(ScraperError):
    """Exception for HTML/data parsing errors."""
    
    def __init__(self, message: str, url: str = "", element: str = "",
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "parsing", context)
        self.url = url
        self.element = element


class ValidationError(ScraperError):
    """Exception for data validation errors."""
    
    def __init__(self, message: str, field: str = "", value: Any = None,
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "validation", context)
        self.field = field
        self.value = value


class CriticalError(ScraperError):
    """Exception for critical system errors that should stop execution."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "critical", context)


def retry_on_error(max_retries: int = 3, backoff_factor: float = 2.0,
                  exceptions: tuple = (RequestException, ConnectionError, Timeout)):
    """
    Decorator for retrying functions on specific exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        exceptions: Tuple of exceptions to catch and retry on
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    # Calculate backoff delay
                    delay = backoff_factor ** attempt
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                except Exception as e:
                    # For non-retryable exceptions, raise immediately
                    raise e
            
            # If we get here, all retries failed
            raise NetworkError(
                f"Function {func.__name__} failed after {max_retries + 1} attempts",
                context={"last_exception": str(last_exception)}
            ) from last_exception
        
        return wrapper
    return decorator


def handle_network_error(func: Callable[..., T]) -> Callable[..., Optional[T]]:
    """
    Decorator for handling network errors gracefully.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that returns None on network errors
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Optional[T]:
        try:
            return func(*args, **kwargs)
        except (ConnectionError, Timeout, HTTPError) as e:
            logging.error(f"Network error in {func.__name__}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {e}")
            return None
    
    return wrapper


def handle_parsing_error(func: Callable[..., T], default_value: T = None) -> Callable[..., T]:
    """
    Decorator for handling parsing errors gracefully.
    
    Args:
        func: Function to wrap
        default_value: Value to return on parsing error
        
    Returns:
        Wrapped function that returns default_value on parsing errors
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except (AttributeError, KeyError, IndexError, ValueError) as e:
            logging.warning(f"Parsing error in {func.__name__}: {e}")
            return default_value
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {e}")
            return default_value
    
    return wrapper


class ErrorRecovery:
    """
    Error recovery utilities for graceful degradation.
    
    Provides methods for handling various error scenarios
    and implementing fallback strategies.
    """
    
    def __init__(self, logger: Optional[ScraperLogger] = None):
        """
        Initialize error recovery handler.
        
        Args:
            logger: ScraperLogger instance for error tracking
        """
        self.logger = logger
        self.recovery_strategies = {
            'network': self._handle_network_recovery,
            'parsing': self._handle_parsing_recovery,
            'validation': self._handle_validation_recovery,
            'critical': self._handle_critical_recovery
        }
    
    def recover_from_error(self, error: ScraperError, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Attempt to recover from an error.
        
        Args:
            error: The error to recover from
            context: Additional context for recovery
            
        Returns:
            True if recovery was successful, False otherwise
        """
        if self.logger:
            self.logger.log_error(error.error_type, str(error), error, context)
        
        recovery_func = self.recovery_strategies.get(error.error_type)
        if recovery_func:
            return recovery_func(error, context)
        
        return False
    
    def _handle_network_recovery(self, error: NetworkError, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle network error recovery."""
        # For network errors, we typically want to retry or skip
        if hasattr(error, 'status_code'):
            if error.status_code == 404:
                # Skip 404 errors - page not found
                if self.logger:
                    self.logger.get_logger().warning(f"Skipping URL due to 404: {error.url}")
                return True
            elif error.status_code == 429:
                # Rate limiting - implement longer backoff
                if self.logger:
                    self.logger.get_logger().warning("Rate limiting detected, implementing backoff")
                time.sleep(30)  # Wait 30 seconds for rate limiting
                return True
        
        return False
    
    def _handle_parsing_recovery(self, error: ParsingError, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle parsing error recovery."""
        # For parsing errors, we typically want to use default values
        if self.logger:
            self.logger.get_logger().warning(f"Using default value for parsing error: {error.element}")
        return True
    
    def _handle_validation_recovery(self, error: ValidationError, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle validation error recovery."""
        # For validation errors, we typically want to use default values
        if self.logger:
            self.logger.get_logger().warning(f"Using default value for validation error: {error.field}")
        return True
    
    def _handle_critical_recovery(self, error: CriticalError, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle critical error recovery."""
        # Critical errors typically cannot be recovered from
        if self.logger:
            self.logger.get_logger().critical(f"Critical error encountered: {error}")
        return False


class GracefulDegradation:
    """
    Utilities for graceful degradation when errors occur.
    
    Provides methods for handling missing data and implementing
    fallback strategies to keep the scraper running.
    """
    
    def __init__(self, default_values: Optional[Dict[str, Any]] = None):
        """
        Initialize graceful degradation handler.
        
        Args:
            default_values: Dictionary of default values for missing data
        """
        from ..config.settings import DEFAULT_VALUES
        self.default_values = default_values or DEFAULT_VALUES
    
    def get_safe_value(self, key: str, value: Any, fallback: Optional[str] = None) -> str:
        """
        Get a safe value with fallback to defaults.
        
        Args:
            key: The field key
            value: The original value
            fallback: Custom fallback value
            
        Returns:
            Safe value or default
        """
        if value is None or value == "":
            return fallback or self.default_values.get(key, "Unknown")
        
        if isinstance(value, str):
            return value.strip()
        
        return str(value)
    
    def extract_with_fallback(self, soup: BeautifulSoup, selector: str, 
                            attribute: Optional[str] = None, 
                            default: str = "Unknown") -> str:
        """
        Extract data from HTML with fallback to default.
        
        Args:
            soup: BeautifulSoup object
            selector: CSS selector
            attribute: HTML attribute to extract (optional)
            default: Default value if extraction fails
            
        Returns:
            Extracted value or default
        """
        try:
            element = soup.select_one(selector)
            if element:
                if attribute:
                    return element.get(attribute, default)
                else:
                    return element.get_text(strip=True) or default
        except Exception as e:
            logging.warning(f"Failed to extract {selector}: {e}")
        
        return default
    
    def safe_json_extract(self, data: Dict[str, Any], key_path: str, 
                         default: Any = None) -> Any:
        """
        Safely extract nested JSON data.
        
        Args:
            data: JSON data dictionary
            key_path: Dot-separated key path (e.g., "user.profile.name")
            default: Default value if extraction fails
            
        Returns:
            Extracted value or default
        """
        try:
            keys = key_path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            
            return current
        except Exception as e:
            logging.warning(f"Failed to extract JSON path {key_path}: {e}")
            return default


def setup_error_handling(logger: Optional[ScraperLogger] = None) -> tuple[ErrorRecovery, GracefulDegradation]:
    """
    Set up error handling components.
    
    Args:
        logger: ScraperLogger instance
        
    Returns:
        Tuple of (ErrorRecovery, GracefulDegradation) instances
    """
    error_recovery = ErrorRecovery(logger)
    graceful_degradation = GracefulDegradation()
    
    return error_recovery, graceful_degradation


def log_and_continue(func: Callable[..., T], logger: Optional[logging.Logger] = None) -> Callable[..., Optional[T]]:
    """
    Decorator that logs errors and continues execution.
    
    Args:
        func: Function to wrap
        logger: Logger instance
        
    Returns:
        Wrapped function that logs errors and returns None on failure
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Optional[T]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if logger:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            else:
                logging.error(f"Error in {func.__name__}: {e}", exc_info=True)
            return None
    
    return wrapper