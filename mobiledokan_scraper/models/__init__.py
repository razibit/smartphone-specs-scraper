"""
Data models module for MobileDokan scraper.

Contains data structures and validation logic for phone specifications.
"""

from .phone_data import PhoneSpecifications, PhoneDataValidator, validate_phone_list

__all__ = ['PhoneSpecifications', 'PhoneDataValidator', 'validate_phone_list']