from digster_api import __version__
from digster_api.example import multiply_two_numbers
from digster_api.main import root


def test_root():
    result = root()
    assert result.get("message") == "Hello World"


def test_multiply_two_numbers():
    result = multiply_two_numbers(2, 3)
    assert result == 6


def test_version():
    assert __version__ == "0.1.0"
