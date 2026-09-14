#!/usr/bin/env python3
"""
Main entry point for MobileDokan scraper.

This module orchestrates the complete scraping workflow:
1. URL extraction from category pages
2. Detail scraping from individual phone pages
3. Data export to JSON and CSV formats

The scraper includes comprehensive error handling, progress tracking,
and logging throughout the process.
"""

import sys
import logging
import argparse
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from mobiledokan_scraper.utils.http_client import HTTPClient
from mobiledokan_scraper.scrapers.listing_scraper import ListingScraper
from mobiledokan_scraper.scrapers.detail_scraper import DetailScraper
from mobiledokan_scraper.utils.file_manager import FileManager
from mobiledokan_scraper.models.phone_data import PhoneSpecifications
from mobiledokan_scraper.utils.logging_config import setup_logging, ProgressTracker
from mobiledokan_scraper.utils.error_handling import (
    setup_error_handling, 
    ScraperError, 
    NetworkError, 
    ParsingError, 
    CriticalError,
    retry_on_error
)
from mobiledokan_scraper.config.settings import (
    BASE_URL, 
    LOG_LEVEL, 
    LOG_FORMAT, 
    LOG_FILE,
    BATCH_SIZE,
    PROGRESS_UPDATE_INTERVAL
)


class MobileDokanScraper:
    """
    Main orchestrator for the MobileDokan scraping workflow.
    
    Coordinates all scraping components and manages the complete workflow
    from URL extraction to data export with comprehensive error handling
    and progress tracking.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the scraper with all required components.
        
        Args:
            output_dir: Custom output directory for saved files
        """
        # Set up comprehensive logging
        self.scraper_logger = setup_logging()
        self.logger = self.scraper_logger.get_logger()
        
        # Set up error handling
        self.error_recovery, self.graceful_degradation = setup_error_handling(self.scraper_logger)
        
        # Initialize components
        self.http_client = HTTPClient()
        self.listing_scraper = ListingScraper(self.http_client)
        self.detail_scraper = DetailScraper(self.http_client)
        self.file_manager = FileManager(output_dir)
        
        # Progress tracking
        self.total_phones = 0
        self.processed_phones = 0
        self.successful_scrapes = 0
        self.failed_scrapes = 0
        self.progress_tracker = None
        
        self.logger.info("MobileDokan scraper initialized successfully")
    
    @retry_on_error(max_retries=2, backoff_factor=1.5)
    def _safe_extract_phone_urls(self, base_url: str) -> List[dict]:
        """
        Safely extract phone URLs with error handling and retries.
        
        Args:
            base_url: Base URL for smartphone category
            
        Returns:
            List of phone URL dictionaries
        """
        try:
            return self.listing_scraper.scrape_all_phone_urls(base_url)
        except Exception as e:
            # Convert to our custom exception for better error handling
            raise NetworkError(f"Failed to extract phone URLs from {base_url}", url=base_url) from e
    
    def run_complete_scraping(self, base_url: str = BASE_URL, 
                            max_phones: Optional[int] = None,
                            start_page: int = 1) -> dict:
        """
        Execute the complete scraping workflow.
        
        Args:
            base_url: Base URL for smartphone category
            max_phones: Maximum number of phones to scrape (None for all)
            start_page: Page number to start scraping from
            
        Returns:
            Dictionary with scraping results and statistics
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting MobileDokan scraping workflow")
        self.logger.info("=" * 60)
        
        try:
            # Phase 1: Extract phone URLs
            self.logger.info("Phase 1: Extracting phone URLs from category pages")
            phone_urls = self._extract_phone_urls(base_url, max_phones, start_page)
            
            if not phone_urls:
                self.logger.error("No phone URLs found. Aborting scraping process.")
                return self._create_results_summary(success=False)
            
            self.total_phones = len(phone_urls)
            self.logger.info(f"Found {self.total_phones} phone URLs to scrape")
            
            # Phase 2: Scrape detailed specifications
            self.logger.info("Phase 2: Scraping detailed phone specifications")
            phone_specifications = self._scrape_phone_details(phone_urls, max_phones)
            
            if not phone_specifications:
                self.logger.error("No phone specifications scraped successfully.")
                return self._create_results_summary(success=False)
            
            # Phase 3: Export data
            self.logger.info("Phase 3: Exporting scraped data")
            export_results = self._export_data(phone_specifications)
            
            # Create final results summary
            results = self._create_results_summary(
                success=True,
                phone_specifications=phone_specifications,
                export_results=export_results
            )
            
            self._log_final_summary(results)
            return results
            
        except KeyboardInterrupt:
            self.logger.warning("Scraping interrupted by user")
            return self._create_results_summary(success=False, interrupted=True)
        except Exception as e:
            self.logger.error(f"Critical error in scraping workflow: {e}", exc_info=True)
            return self._create_results_summary(success=False, error=str(e))
        finally:
            self._cleanup()
    
    def _extract_phone_urls(self, base_url: str, max_phones: Optional[int], 
                          start_page: int) -> List[dict]:
        """
        Extract phone URLs from category pages with comprehensive error handling.
        
        Args:
            base_url: Base URL for smartphone category
            max_phones: Maximum number of phones to extract
            start_page: Page number to start from
            
        Returns:
            List of phone URL dictionaries
        """
        try:
            # Modify base URL if starting from a specific page
            if start_page > 1:
                scrape_url = f"{base_url}?page={start_page}"
            else:
                scrape_url = base_url
            
            self.logger.info(f"Starting URL extraction from: {scrape_url}")
            
            # If max_phones is specified and small, use optimized extraction
            if max_phones and max_phones <= 50:
                phone_urls = self._extract_phone_urls_limited(scrape_url, max_phones)
            else:
                phone_urls = self._safe_extract_phone_urls(scrape_url)
                
                # Limit results if max_phones is specified
                if max_phones and len(phone_urls) > max_phones:
                    phone_urls = phone_urls[:max_phones]
                    self.logger.info(f"Limited results to {max_phones} phones as requested")
            
            self.logger.info(f"Successfully extracted {len(phone_urls)} phone URLs")
            return phone_urls
            
        except NetworkError as e:
            self.scraper_logger.log_error("network_errors", str(e), e, {"url": e.url})
            if self.error_recovery.recover_from_error(e):
                return []  # Continue with empty list if recovery is possible
            raise
        except Exception as e:
            error = CriticalError(f"Critical error in URL extraction: {e}")
            self.scraper_logger.log_error("critical_errors", str(error), e)
            return []
    
    def _extract_phone_urls_limited(self, base_url: str, max_phones: int) -> List[dict]:
        """
        Extract a limited number of phone URLs efficiently.
        
        Args:
            base_url: Base URL for smartphone category
            max_phones: Maximum number of phones to extract
            
        Returns:
            List of phone URL dictionaries (limited to max_phones)
        """
        phone_urls = []
        current_page = 1
        
        # Extract the base URL without page parameter
        if '?page=' in base_url:
            base_url_clean = base_url.split('?page=')[0]
            current_page = int(base_url.split('?page=')[1])
        else:
            base_url_clean = base_url
        
        self.logger.info(f"Extracting up to {max_phones} phone URLs efficiently")
        
        while len(phone_urls) < max_phones:
            # Construct URL for current page
            if current_page == 1:
                page_url = base_url_clean
            else:
                page_url = f"{base_url_clean}?page={current_page}"
            
            self.logger.info(f"Scraping page {current_page}: {page_url}")
            
            try:
                # Get the page content
                response = self.http_client.get(page_url)
                html_content = response.text
                
                # Extract phone URLs from this page
                page_phones = self.listing_scraper.extract_phone_urls_from_page(html_content)
                
                if not page_phones:
                    self.logger.info(f"No phones found on page {current_page}, stopping extraction")
                    break
                
                # Add phones up to the limit
                remaining_slots = max_phones - len(phone_urls)
                phones_to_add = page_phones[:remaining_slots]
                phone_urls.extend(phones_to_add)
                
                self.logger.info(f"Found {len(page_phones)} phones on page {current_page}, "
                               f"added {len(phones_to_add)} (total: {len(phone_urls)})")
                
                # Stop if we have enough phones
                if len(phone_urls) >= max_phones:
                    break
                
                current_page += 1
                
            except Exception as e:
                self.logger.error(f"Error scraping page {current_page}: {e}")
                break
        
        return phone_urls
    
    def _scrape_phone_details(self, phone_urls: List[dict], 
                            max_phones: Optional[int]) -> List[PhoneSpecifications]:
        """
        Scrape detailed specifications for each phone with comprehensive error handling.
        
        Args:
            phone_urls: List of phone URL dictionaries
            max_phones: Maximum number of phones to process
            
        Returns:
            List of successfully scraped phone specifications
        """
        phone_specifications = []
        
        # Limit processing if max_phones is specified
        urls_to_process = phone_urls[:max_phones] if max_phones else phone_urls
        
        self.logger.info(f"Starting detail scraping for {len(urls_to_process)} phones")
        
        # Initialize progress tracker
        self.progress_tracker = ProgressTracker(
            self.scraper_logger, 
            len(urls_to_process), 
            "Scraping phone details"
        )
        
        for i, phone_info in enumerate(urls_to_process, 1):
            try:
                # Extract required information
                detail_url = phone_info.get('detail_url', '')
                image_url = phone_info.get('image_url', '')
                
                if not detail_url:
                    error = ParsingError("No detail URL found", element="detail_url")
                    self.scraper_logger.log_error("parsing_errors", str(error), error)
                    self.failed_scrapes += 1
                    self.progress_tracker.update(additional_info="Missing URL")
                    continue
                
                self.logger.debug(f"Scraping phone {i}/{len(urls_to_process)}: {detail_url}")
                
                # Scrape phone specifications with error handling
                phone_specs = self._safe_scrape_phone_details(detail_url, image_url)
                
                if phone_specs:
                    # Add additional metadata from listing
                    self._enrich_phone_specs(phone_specs, phone_info)
                    phone_specifications.append(phone_specs)
                    self.successful_scrapes += 1
                    
                    self.logger.debug(f"Successfully scraped: {phone_specs.brand} {phone_specs.model}")
                    self.progress_tracker.update(additional_info=f"{phone_specs.brand} {phone_specs.model}")
                else:
                    self.failed_scrapes += 1
                    self.logger.warning(f"Failed to scrape specifications for: {detail_url}")
                    self.progress_tracker.update(additional_info="Failed")
                
                self.processed_phones += 1
                
                # Process in batches to manage memory
                if i % BATCH_SIZE == 0:
                    self.logger.info(f"Processed batch of {BATCH_SIZE} phones. "
                                   f"Success: {self.successful_scrapes}, Failed: {self.failed_scrapes}")
                
            except KeyboardInterrupt:
                self.logger.warning("Detail scraping interrupted by user")
                break
            except NetworkError as e:
                self.scraper_logger.log_error("network_errors", str(e), e, {"url": e.url})
                if self.error_recovery.recover_from_error(e):
                    self.failed_scrapes += 1
                    self.processed_phones += 1
                    self.progress_tracker.update(additional_info="Network error")
                    continue
                else:
                    break
            except Exception as e:
                self.failed_scrapes += 1
                self.processed_phones += 1
                self.scraper_logger.log_error("parsing_errors", f"Error scraping phone {i}: {e}", e)
                self.progress_tracker.update(additional_info="Error")
                continue
        
        # Complete progress tracking
        if self.progress_tracker:
            self.progress_tracker.complete(f"Scraped {len(phone_specifications)} phones successfully")
        
        self.logger.info(f"Detail scraping completed. "
                        f"Successfully scraped: {len(phone_specifications)} phones")
        
        return phone_specifications
    
    def _safe_scrape_phone_details(self, detail_url: str, image_url: str) -> Optional[PhoneSpecifications]:
        """
        Safely scrape phone details with error handling.
        
        Args:
            detail_url: URL of the phone detail page
            image_url: URL of the phone image
            
        Returns:
            PhoneSpecifications object or None if scraping failed
        """
        try:
            return self.detail_scraper.scrape_phone_details(detail_url, image_url)
        except Exception as e:
            # Use graceful degradation to handle errors
            error = ParsingError(f"Failed to scrape phone details: {e}", url=detail_url)
            if self.error_recovery.recover_from_error(error):
                # Return a minimal phone specification with available data
                phone_specs = PhoneSpecifications()
                phone_specs.detail_url = detail_url
                phone_specs.image_url = image_url
                phone_specs.scraped_at = datetime.now().isoformat()
                return phone_specs
            return None
    
    def _enrich_phone_specs(self, phone_specs: PhoneSpecifications, phone_info: dict) -> None:
        """
        Enrich phone specifications with additional data from listing.
        
        Args:
            phone_specs: Phone specifications object to enrich
            phone_info: Additional phone information from listing
        """
        # Add listing data if not already present in detailed specs
        if not phone_specs.brand and phone_info.get('brand'):
            phone_specs.brand = phone_info['brand']
        
        if not phone_specs.model and phone_info.get('title'):
            phone_specs.model = phone_info['title']
        
        # Add metadata that might not be in detail page
        if phone_info.get('ram'):
            phone_specs.ram = phone_info['ram']
        
        if phone_info.get('storage'):
            phone_specs.internal_storage = phone_info['storage']
        
        if phone_info.get('display'):
            phone_specs.screen_size = phone_info['display']
        
        if phone_info.get('main_camera'):
            phone_specs.primary_camera_resolution = phone_info['main_camera']
        
        if phone_info.get('battery'):
            phone_specs.battery_capacity = phone_info['battery']
        
        if phone_info.get('os'):
            phone_specs.operating_system = phone_info['os']
    
    def _export_data(self, phone_specifications: List[PhoneSpecifications]) -> dict:
        """
        Export scraped data to JSON and CSV formats.
        
        Args:
            phone_specifications: List of phone specifications to export
            
        Returns:
            Dictionary with export results
        """
        try:
            self.logger.info(f"Exporting {len(phone_specifications)} phone specifications")
            
            # Save to both JSON and CSV formats
            export_paths = self.file_manager.save_phone_specifications(
                phone_specifications,
                include_timestamp=True
            )
            
            # Log export results
            for format_type, file_path in export_paths.items():
                file_size = file_path.stat().st_size
                self.logger.info(f"Exported {format_type.upper()}: {file_path} ({file_size:,} bytes)")
            
            return {
                'success': True,
                'files': export_paths,
                'record_count': len(phone_specifications)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'record_count': len(phone_specifications)
            }
    
    def _update_progress(self, current: int, total: int) -> None:
        """
        Update and log progress information.
        
        Args:
            current: Current item number
            total: Total number of items
        """
        if current % PROGRESS_UPDATE_INTERVAL == 0 or current == total:
            progress_percent = (current / total) * 100
            self.logger.info(f"Progress: {current}/{total} ({progress_percent:.1f}%) - "
                           f"Success: {self.successful_scrapes}, Failed: {self.failed_scrapes}")
    
    def _create_results_summary(self, success: bool, phone_specifications: Optional[List] = None,
                              export_results: Optional[dict] = None, interrupted: bool = False,
                              error: Optional[str] = None) -> dict:
        """
        Create a comprehensive results summary.
        
        Args:
            success: Whether the overall operation was successful
            phone_specifications: List of scraped phone specifications
            export_results: Results from data export
            interrupted: Whether the operation was interrupted
            error: Error message if operation failed
            
        Returns:
            Dictionary with complete results summary
        """
        return {
            'success': success,
            'interrupted': interrupted,
            'error': error,
            'statistics': {
                'total_phones_found': self.total_phones,
                'phones_processed': self.processed_phones,
                'successful_scrapes': self.successful_scrapes,
                'failed_scrapes': self.failed_scrapes,
                'success_rate': (self.successful_scrapes / max(self.processed_phones, 1)) * 100
            },
            'scraped_data': phone_specifications or [],
            'export_results': export_results or {},
            'timestamp': datetime.now().isoformat()
        }
    
    def _log_final_summary(self, results: dict) -> None:
        """
        Log a comprehensive final summary of the scraping operation.
        
        Args:
            results: Results dictionary from scraping operation
        """
        # Use the comprehensive logging system
        stats = results['statistics']
        
        # Log detailed statistics
        self.scraper_logger.log_statistics({
            'Total phones found': stats['total_phones_found'],
            'Phones processed': stats['phones_processed'],
            'Successful scrapes': stats['successful_scrapes'],
            'Failed scrapes': stats['failed_scrapes'],
            'Success rate': f"{stats['success_rate']:.1f}%"
        })
        
        if results['export_results'].get('success'):
            export_files = results['export_results'].get('files', {})
            self.logger.info("Exported files:")
            for format_type, file_path in export_files.items():
                self.logger.info(f"  {format_type.upper()}: {file_path}")
        
        if results['interrupted']:
            self.logger.warning("Operation was interrupted by user")
        elif results['error']:
            self.logger.error(f"Operation failed with error: {results['error']}")
        elif results['success']:
            self.logger.info("Scraping workflow completed successfully!")
    
    def _cleanup(self) -> None:
        """Clean up resources and close connections."""
        try:
            if hasattr(self, 'http_client'):
                self.http_client.close()
            self.logger.info("Cleanup completed successfully")
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="MobileDokan smartphone scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Scrape all phones
  python main.py --max-phones 50          # Scrape first 50 phones
  python main.py --start-page 5           # Start from page 5
  python main.py --output-dir ./data      # Custom output directory
  python main.py --max-phones 100 --start-page 2  # Combined options
        """
    )
    
    parser.add_argument(
        '--max-phones',
        type=int,
        help='Maximum number of phones to scrape (default: all)'
    )
    
    parser.add_argument(
        '--start-page',
        type=int,
        default=1,
        help='Page number to start scraping from (default: 1)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for scraped data (default: ./output)'
    )
    
    parser.add_argument(
        '--base-url',
        type=str,
        default=BASE_URL,
        help=f'Base URL for smartphone category (default: {BASE_URL})'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=LOG_LEVEL,
        help=f'Logging level (default: {LOG_LEVEL})'
    )
    
    return parser


def main():
    """Main entry point for the scraper application."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Update log level if specified
    if args.log_level != LOG_LEVEL:
        import mobiledokan_scraper.config.settings as settings
        settings.LOG_LEVEL = args.log_level
    
    try:
        # Initialize and run scraper
        scraper = MobileDokanScraper(output_dir=args.output_dir)
        
        results = scraper.run_complete_scraping(
            base_url=args.base_url,
            max_phones=args.max_phones,
            start_page=args.start_page
        )
        
        # Exit with appropriate code
        if results['success'] and not results['interrupted']:
            sys.exit(0)
        elif results['interrupted']:
            sys.exit(130)  # Standard exit code for SIGINT
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()