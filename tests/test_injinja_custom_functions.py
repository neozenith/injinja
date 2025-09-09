"""Tests for custom function loading."""

# Our Libraries
from injinja.injinja import get_functions


class TestCustomFunctions:
    """Test custom function loading."""

    def test_get_functions(self, tmp_path):
        """Test get_functions loads custom functions from Python files."""
        func_file = tmp_path / "get_functions_functions.py"
        func_file.write_text("""
def test_custom():
    return True

def filter_uppercase(value):
    return value.upper()

def regular_function():
    return "not included"
""")

        result = get_functions([str(func_file)])
        assert "custom" in result["tests"]
        assert "uppercase" in result["filters"]
        assert "regular_function" not in result["tests"]
        assert "regular_function" not in result["filters"]

    def test_get_functions_empty(self):
        """Test get_functions with no function files."""
        result = get_functions([])
        assert result == {"tests": {}, "filters": {}}
