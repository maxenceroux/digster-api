from digster_api import __version__
from digster_api.math import multiply_two_numbers


def test_multiply_two_numbers():
    result = multiply_two_numbers(2, 3)
    assert result == 6


def test_version():
    assert __version__ == "0.1.0"
