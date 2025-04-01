import pytest
from src.routers.user import is_valid_url, is_valid_short_code, is_valid_date_format


@pytest.mark.parametrize("url, expected", [
    ("https://google.com", True),
    ("http://example.com/path?query=param", True),
    ("not-a-url", False),
    ("ftp://invalid.scheme", False),
    ("https://", False),
    (None, False),
    ("", False)
])
def test_url_validation(url, expected):
    assert is_valid_url(url) == expected


@pytest.mark.parametrize("name, expected", [
    ("valid_name123", True),
    ("VALID-NAME", True),
    ("a", True),
    ("invalid name", False),
    ("invalid@name", False),
    ("invalid/name", False)
])
def test_short_name_validation(name, expected):
    assert is_valid_short_code(name) == expected


@pytest.mark.parametrize("date_str, expected", [
    ("2023-12-31", True),
    ("2023-12-31 23", True),
    ("2023-12-31 23:59", True),
    ("31-12-2023", False),
    ("2023/12/31", False),
    ("2023-12-31 23:59:00", False),
    ("not-a-date", False)
])
def test_date_validation(date_str, expected):
    assert is_valid_date_format(date_str) == expected