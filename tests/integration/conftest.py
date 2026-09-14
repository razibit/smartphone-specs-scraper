"""
Configuration and fixtures for integration tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_fixtures():
    """Load sample HTML fixtures for testing."""
    fixtures_dir = Path('tests/fixtures')
    
    fixtures = {}
    fixture_files = [
        'sample_listing_page.html',
        'sample_detail_page.html',
        'sample_empty_page.html',
        'sample_malformed_page.html',
        'sample_network_error_page.html'
    ]
    
    for fixture_file in fixture_files:
        fixture_path = fixtures_dir / fixture_file
        if fixture_path.exists():
            with open(fixture_path, 'r', encoding='utf-8') as f:
                fixtures[fixture_file.replace('.html', '')] = f.read()
    
    return fixtures


@pytest.fixture
def expected_data():
    """Load expected test data for validation."""
    expected_file = Path('tests/fixtures/expected_phone_data.json')
    if expected_file.exists():
        import json
        with open(expected_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


@pytest.fixture
def mock_http_responses(sample_fixtures):
    """Create mock HTTP responses for testing."""
    def create_mock_response(content, status_code=200):
        mock_response = Mock()
        mock_response.text = content
        mock_response.content = content.encode('utf-8') if isinstance(content, str) else content
        mock_response.status_code = status_code
        mock_response.raise_for_status = Mock()
        mock_response.headers = {}
        mock_response.url = "http://test.com"
        if status_code >= 400:
            import requests
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(f"{status_code} Error")
        return mock_response
    
    return {
        'listing_success': create_mock_response(sample_fixtures.get('sample_listing_page', '')),
        'listing_success_extended': create_mock_response('''
<!DOCTYPE html>
<html>
<body>
    <script>
        let productDataArray = {
            "current_page": 1,
            "last_page": 1,
            "data": [
                {"type": "mobile", "title": "Infinix Smart 8 Pro", "slug": "infinix-smart-8-pro"},
                {"type": "mobile", "title": "Google Pixel 7", "slug": "google-pixel-7"},
                {"type": "mobile", "title": "Samsung Galaxy S24", "slug": "samsung-galaxy-s24"},
                {"type": "mobile", "title": "Apple iPhone 15", "slug": "iphone-15"}
            ]
        };
    </script>
</body>
</html>
'''),
        'detail_success': create_mock_response(sample_fixtures.get('sample_detail_page', '')),
        'empty_page': create_mock_response(sample_fixtures.get('sample_empty_page', '')),
        'malformed_page': create_mock_response(sample_fixtures.get('sample_malformed_page', '')),
        'network_error': create_mock_response(sample_fixtures.get('sample_network_error_page', ''), 503),
        'not_found': create_mock_response('<html><body>404 Not Found</body></html>', 404),
        'rate_limited': create_mock_response('<html><body>429 Too Many Requests</body></html>', 429)
    }


@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    return {
        'max_test_phones': 5,
        'test_timeout': 30,
        'expected_success_rate': 0.8,  # 80% success rate threshold
        'batch_size': 2
    }
