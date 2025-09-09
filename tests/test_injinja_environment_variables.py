"""Tests for environment variable handling functions."""

# Standard Library
from unittest.mock import patch

# Our Libraries
from injinja.injinja import (
    dict_from_keyvalue_list,
    dict_from_prefixes,
    get_environment_variables,
    read_env_file,
)


class TestEnvironmentVariables:
    """Test environment variable handling functions."""

    def test_dict_from_keyvalue_list(self):
        """Test dict_from_keyvalue_list converts key=value strings."""
        result = dict_from_keyvalue_list(["KEY1=value1", "KEY2=value2"])
        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_dict_from_keyvalue_list_none(self):
        """Test dict_from_keyvalue_list with None input."""
        result = dict_from_keyvalue_list(None)
        assert result is None

    def test_read_env_file(self, tmp_path):
        """Test read_env_file reads .env files correctly."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=value2\n# Comment\nKEY3=value3")

        result = read_env_file(str(env_file))
        assert result == {"KEY1": "value1", "KEY2": "value2", "KEY3": "value3"}

    def test_read_env_file_nonexistent(self):
        """Test read_env_file returns None for nonexistent file."""
        result = read_env_file("/nonexistent/file.env")
        assert result is None

    def test_dict_from_prefixes(self):
        """Test dict_from_prefixes extracts prefixed env vars."""
        with patch.dict("os.environ", {"PREFIX_VAR1": "value1", "PREFIX_VAR2": "value2", "OTHER": "value3"}):
            result = dict_from_prefixes(["PREFIX_"])
            assert result is not None
            assert "PREFIX_VAR1" in result
            assert "PREFIX_VAR2" in result
            assert "OTHER" not in result

    def test_dict_from_prefixes_none(self):
        """Test dict_from_prefixes with None input."""
        result = dict_from_prefixes(None)
        assert result is None

    def test_get_environment_variables(self, tmp_path):
        """Test get_environment_variables merges all sources."""
        # Create a test .env file
        env_file = tmp_path / ".env"
        env_file.write_text("FILE_KEY=file_value")

        with patch.dict("os.environ", {"PREFIX_KEY": "prefix_value"}):
            result = get_environment_variables(
                env_flags=["CLI_KEY=cli_value", str(env_file)], prefixes_list=["PREFIX_"]
            )

            assert result["CLI_KEY"] == "cli_value"
            assert result["FILE_KEY"] == "file_value"
            assert result["PREFIX_KEY"] == "prefix_value"
