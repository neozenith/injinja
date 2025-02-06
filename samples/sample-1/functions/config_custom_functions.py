# Standard Library
import math


def test_is_prime(n):
    if n == 2:
        return True

    return all(n % i != 0 for i in range(2, int(math.ceil(math.sqrt(n))) + 1))


def filter_default_or(value, default):
    """Custom filter to provide default values"""
    return default if value is None else value


def filter_upper_case(value):
    """Convert value to uppercase"""
    return str(value).upper() if value is not None else value
