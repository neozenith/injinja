"""Tests for the main merge function."""

# Standard Library
import json
import textwrap
from unittest.mock import patch

# Third Party
import pytest
import yaml
from jinja2.filters import FILTERS

# Our Libraries
from injinja.injinja import get_functions, merge


class TestMergeFunction:
    """Test the main merge function."""

    def test_merge_basic(self, tmp_path):
        """Test basic merge functionality."""
        template = tmp_path / "template.txt"
        template.write_text("Hello {{ name }}")

        config = tmp_path / "config.json"
        config.write_text('{"name": "World"}')

        result, diff = merge(config=[str(config)], template=str(template))

        assert result == "Hello World"
        assert diff is None

    def test_merge_with_validation(self, tmp_path):
        """Test merge with validation file."""
        template = tmp_path / "template.txt"
        template.write_text("Hello World")

        validate = tmp_path / "validate.txt"
        validate.write_text("Hello World")

        result, diff = merge(template=str(template), validate=str(validate))

        assert result == "Hello World"
        assert diff == ""  # No difference

    def test_merge_output_to_file(self, tmp_path):
        """Test merge outputs to file."""
        template = tmp_path / "template.txt"
        template.write_text("Content")

        output = tmp_path / "output.txt"

        merge(template=str(template), output=str(output))

        assert output.read_text() == "Content"

    def test_merge_config_json_output(self, tmp_path, capsys):
        """Test merge with config-json output."""
        config = tmp_path / "config.json"
        config.write_text('{"key": "value"}')

        merge(config=[str(config)], output="config-json")

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == {"key": "value"}

    def test_merge_config_yaml_output(self, tmp_path, capsys):
        """Test merge with config-yaml output."""
        config = tmp_path / "config.json"
        config.write_text('{"key": "value"}')

        merge(config=[str(config)], output="config-yaml")

        captured = capsys.readouterr()
        output = yaml.safe_load(captured.out)
        assert output == {"key": "value"}

    @pytest.mark.skip(
        reason="""
        Getting inconsistent results across multiple runs. 
        I suspect due to the nature of setting filters in Jinja is modifying a global function
    """
    )
    def test_merge_with_functions(self, tmp_path):
        """Test merge with custom functions."""
        func_file = tmp_path / "merge_with_functions" / "merge_with_functions.py"
        func_file.parent.mkdir(parents=True, exist_ok=True)
        func_file.write_text(
            textwrap.dedent("""
        def filter_lowercase(value):
            return value.lower()
        """)
        )

        # Need non-empty config for Jinja templating environment to be active so that custom functions can be used.
        config = tmp_path / "merge_with_functions" / "merge_with_functions_config.json"
        config.write_text('{"name": "WORLD"}')

        template = tmp_path / "merge_with_functions" / "merge_with_functions_template.txt"
        template.write_text("{{ name | lowercase }}")

        f = get_functions([str(func_file)])
        assert "lowercase" in f["filters"]

        # The jinja2 TESTS and FILTERS dictionary is a global variable we are tweaking here.
        FILTERS.update(f["filters"])

        result, _ = merge(template=str(template), config=[str(config)], functions=[str(func_file)])

        assert "lowercase" in FILTERS
        assert result == "world"

    @patch("sys.stdin")
    def test_merge_with_stdin(self, mock_stdin, tmp_path):
        """Test merge with stdin input."""
        mock_stdin.isatty.return_value = False
        mock_stdin.read.return_value = '{"stdin_key": "stdin_value"}'

        template = tmp_path / "template.txt"
        template.write_text("{{ stdin_key }}")

        result, _ = merge(template=str(template), stdin_format="json")

        assert result == "stdin_value"
