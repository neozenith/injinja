"""Tests for configuration file loading functions."""

# Third Party
import pytest

# Our Libraries
from injinja.injinja import load_config, parse_stdin_content


class TestConfigLoading:
    """Test configuration file loading functions."""

    def test_load_config_json(self, tmp_path):
        """Test load_config with JSON file."""
        json_file = tmp_path / "config.json"
        json_file.write_text('{"key": "value"}')

        result = load_config(str(json_file))
        assert result == {"key": "value"}

    def test_load_config_yaml(self, tmp_path):
        """Test load_config with YAML file."""
        yaml_file = tmp_path / "config.yml"
        yaml_file.write_text("key: value")

        result = load_config(str(yaml_file))
        assert result == {"key": "value"}

    def test_load_config_toml(self, tmp_path):
        """Test load_config with TOML file."""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text('key = "value"')

        result = load_config(str(toml_file))
        assert result == {"key": "value"}

    def test_load_config_with_template(self, tmp_path):
        """Test load_config with Jinja2 templating."""
        json_file = tmp_path / "config.json"
        json_file.write_text('{"key": "{{ var }}"}')

        result = load_config(str(json_file), {"var": "templated_value"})
        assert result == {"key": "templated_value"}

    def test_load_config_unsupported(self, tmp_path):
        """Test load_config raises error for unsupported file type."""
        txt_file = tmp_path / "config.txt"
        txt_file.write_text("content")

        with pytest.raises(ValueError, match="File type.*not supported"):
            load_config(str(txt_file))

    def test_parse_stdin_content(self):
        """Test parse_stdin_content parses different formats."""
        # Test JSON
        result = parse_stdin_content('{"key": "value"}', "json")
        assert result == {"key": "value"}

        # Test YAML
        result = parse_stdin_content("key: value", "yaml")
        assert result == {"key": "value"}

        # Test TOML
        result = parse_stdin_content('key = "value"', "toml")
        assert result == {"key": "value"}

        # Test unsupported format
        with pytest.raises(ValueError, match="Unsupported stdin format"):
            parse_stdin_content("content", "xml")
