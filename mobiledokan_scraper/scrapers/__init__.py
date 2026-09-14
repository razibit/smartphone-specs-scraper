"""
Scrapers package for MobileDokan scraper.

Contains specialized scrapers for different types of pages:
- ListingScraper: Extracts phone URLs from category pages
- DetailScraper: Extracts specifications from individual phone pages
"""

from .listing_scraper import ListingScraper
from .detail_scraper import DetailScraper

__all__ = ['ListingScraper', 'DetailScraper']
