"""
Comprehensive logging configuration for MobileDokan scraper.

This module provides centralized logging configuration with file and console output,
structured logging, and error tracking capabilities.
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..config.settings import LOG_LEVEL, LOG_FORMAT, LOG_FILE, OUTPUT_DIR


class ScraperLogger:
    """
    Centralized logger configuration for the MobileDokan scraper.
    
    Provides structured logging with file rotation, console output,
    and error tracking capabilities.
    """
    
    def __init__(self, name: str = 'mobiledokan_scraper', 
                 log_level: str = LOG_LEVEL,
                 log_file: Optional[str] = None,
                 console_output: bool = True):
        """
        Initialize the scraper logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Custom log file path (optional)
            console_output: Whether to output to console
        """
        self.name = name
        self.log_level = log_level.upper()
        self.log_file = log_file or LOG_FILE
        self.console_output = console_output
        
        # Ensure log directory exists
        self._ensure_log_directory()
        
        # Configure logger
        self.logger = self._setup_logger()
        
        # Error tracking
        self.error_counts = {
            'network_errors': 0,
            'parsing_errors': 0,
            'validation_errors': 0,
            'critical_errors': 0,
            'warnings': 0
        }
        
    def _ensure_log_directory(self) -> None:
        """Ensure the log directory exists."""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _setup_logger(self) -> logging.Logger:
        """
        Set up the logger with file and console handlers.
        
        Returns:
            Configured logger instance
        """
        # Create logger
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.log_level))
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            LOG_FORMAT,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        if self.log_file:
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    self.log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not create log file {self.log_file}: {e}")
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Use colored formatter for console if available
            try:
                console_formatter = ColoredFormatter(
                    LOG_FORMAT,
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_handler.setFormatter(console_formatter)
            except:
                console_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
        
        return logger
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger
    
    def log_error(self, error_type: str, message: str, exception: Optional[Exception] = None,
                  context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error with categorization and context.
        
        Args:
            error_type: Type of error (network, parsing, validation, critical)
            message: Error message
            exception: Exception object (optional)
            context: Additional context information
        """
        # Update error counts
        if error_type in self.error_counts:
            self.error_counts[error_type] += 1
        
        # Prepare log message
        log_message = f"[{error_type.upper()}] {message}"
        
        # Add context if provided
        if context:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            log_message += f" | Context: {context_str}"
        
        # Log with appropriate level
        if error_type == 'critical_errors':
            if exception:
                self.logger.critical(log_message, exc_info=exception)
            else:
                self.logger.critical(log_message)
        elif error_type == 'warnings':
            self.logger.warning(log_message)
        else:
            if exception:
                self.logger.error(log_message, exc_info=exception)
            else:
                self.logger.error(log_message)
    
    def log_progress(self, current: int, total: int, operation: str = "Processing",
                    additional_info: Optional[str] = None) -> None:
        """
        Log progress information.
        
        Args:
            current: Current item number
            total: Total number of items
            operation: Description of the operation
            additional_info: Additional information to include
        """
        percentage = (current / total) * 100 if total > 0 else 0
        
        message = f"{operation}: {current}/{total} ({percentage:.1f}%)"
        if additional_info:
            message += f" - {additional_info}"
        
        self.logger.info(message)
    
    def log_statistics(self, stats: Dict[str, Any]) -> None:
        """
        Log statistics information.
        
        Args:
            stats: Dictionary containing statistics
        """
        self.logger.info("=== STATISTICS ===")
        for key, value in stats.items():
            self.logger.info(f"{key}: {value}")
        
        # Log error summary
        if any(count > 0 for count in self.error_counts.values()):
            self.logger.info("=== ERROR SUMMARY ===")
            for error_type, count in self.error_counts.items():
                if count > 0:
                    self.logger.info(f"{error_type}: {count}")
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors encountered."""
        return self.error_counts.copy()
    
    def reset_error_counts(self) -> None:
        """Reset error counters."""
        for key in self.error_counts:
            self.error_counts[key] = 0


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output.
    
    Adds color coding to different log levels for better readability.
    """
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        # Get the original formatted message
        message = super().format(record)
        
        # Add color if supported
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            return f"{color}{message}{reset}"
        
        return message


class ProgressTracker:
    """
    Progress tracking utility with logging integration.
    
    Provides progress tracking with configurable update intervals
    and automatic logging.
    """
    
    def __init__(self, logger: ScraperLogger, total: int, 
                 operation: str = "Processing", update_interval: int = 10):
        """
        Initialize progress tracker.
        
        Args:
            logger: ScraperLogger instance
            total: Total number of items to process
            operation: Description of the operation
            update_interval: Update progress every N items
        """
        self.logger = logger
        self.total = total
        self.operation = operation
        self.update_interval = update_interval
        self.current = 0
        self.start_time = datetime.now()
        self.last_update = 0
        
    def update(self, increment: int = 1, additional_info: Optional[str] = None) -> None:
        """
        Update progress counter.
        
        Args:
            increment: Number to increment by
            additional_info: Additional information to log
        """
        self.current += increment
        
        # Log progress if interval reached or completed
        if (self.current - self.last_update >= self.update_interval or 
            self.current >= self.total):
            
            # Calculate ETA
            elapsed = datetime.now() - self.start_time
            if self.current > 0:
                eta_seconds = (elapsed.total_seconds() / self.current) * (self.total - self.current)
                eta = f"ETA: {int(eta_seconds//60)}m {int(eta_seconds%60)}s"
            else:
                eta = "ETA: Unknown"
            
            info = f"{eta}"
            if additional_info:
                info += f", {additional_info}"
            
            self.logger.log_progress(self.current, self.total, self.operation, info)
            self.last_update = self.current
    
    def complete(self, final_message: Optional[str] = None) -> None:
        """
        Mark progress as complete.
        
        Args:
            final_message: Final message to log
        """
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"Completed in {int(elapsed.total_seconds()//60)}m {int(elapsed.total_seconds()%60)}s"
        
        message = elapsed_str
        if final_message:
            message += f" - {final_message}"
        
        self.logger.log_progress(self.current, self.total, self.operation, message)


def setup_logging(name: str = 'mobiledokan_scraper', 
                 log_level: str = LOG_LEVEL,
                 log_file: Optional[str] = None) -> ScraperLogger:
    """
    Set up logging for the scraper application.
    
    Args:
        name: Logger name
        log_level: Logging level
        log_file: Custom log file path
        
    Returns:
        Configured ScraperLogger instance
    """
    return ScraperLogger(name=name, log_level=log_level, log_file=log_file)


def get_logger(name: str = 'mobiledokan_scraper') -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)