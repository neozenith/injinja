"""Tests for the injinja module."""

import json
import pathlib
import shutil
import textwrap
from unittest.mock import patch

import pytest
import yaml
from jinja2.filters import FILTERS
from jinja2.tests import TESTS

from injinja.injinja import (
    expand_files_list,
    dict_from_keyvalue_list,
    dict_from_prefixes,
    get_environment_variables,
    get_functions,
    load_config,
    main,
    map_env_to_confs,
    merge,
    merge_template,
    parse_stdin_content,
    read_env_file,
    reduce_confs
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
                env_flags=["CLI_KEY=cli_value", str(env_file)],
                prefixes_list=["PREFIX_"]
            )
            
            assert result["CLI_KEY"] == "cli_value"
            assert result["FILE_KEY"] == "file_value"
            assert result["PREFIX_KEY"] == "prefix_value"


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


class TestTemplating:
    """Test template merging functions."""

    def test_merge_template_without_config(self, tmp_path):
        """Test merge_template without configuration."""
        template_file = tmp_path / "template.txt"
        template_file.write_text("Hello World")
        
        result = merge_template(str(template_file), None)
        assert result == "Hello World"

    def test_merge_template_with_config(self, tmp_path):
        """Test merge_template with configuration."""
        template_file = tmp_path / "template.txt"
        template_file.write_text("Hello {{ name }}")
        
        result = merge_template(str(template_file), {"name": "Test"})
        assert result == "Hello Test"

    # Commented out - Jinja2 version-specific behavior varies
    # def test_merge_template_undefined_error(self, tmp_path):
    #     """Test merge_template raises error for undefined variables in Jinja2 v3+."""
    #     template_file = tmp_path / "template.txt"
    #     template_file.write_text("Hello {{ undefined_var }}")
    #     
    #     # Test with Jinja2 v3+ where StrictUndefined is used
    #     import jinja2
    #     if int(jinja2.__version__[0]) >= 3:
    #         with pytest.raises(jinja2.exceptions.UndefinedError):
    #             merge_template(str(template_file), {})
    #     else:
    #         # In older versions, it doesn't raise by default
    #         result = merge_template(str(template_file), {})
    #         assert "undefined_var" in result  # Variable remains in template


class TestConfigMerging:
    """Test configuration merging functions."""

    def test_map_env_to_confs(self, tmp_path):
        """Test map_env_to_confs loads and templates configs."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "{{ env_var }}"}')
        
        result = map_env_to_confs([str(config_file)], {"env_var": "value"})
        assert result == [{"key": "value"}]

    def test_reduce_confs(self):
        """Test reduce_confs merges configurations."""
        confs = [
            {"key1": "value1", "shared": "first"},
            {"key2": "value2", "shared": "second"}
        ]
        
        result = reduce_confs(confs)
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert result["shared"] == "second"  # Later configs override


class TestMergeFunction:
    """Test the main merge function."""

    def test_merge_basic(self, tmp_path):
        """Test basic merge functionality."""
        template = tmp_path / "template.txt"
        template.write_text("Hello {{ name }}")
        
        config = tmp_path / "config.json"
        config.write_text('{"name": "World"}')
        
        result, diff = merge(
            config=[str(config)],
            template=str(template)
        )
        
        assert result == "Hello World"
        assert diff is None

    def test_merge_with_validation(self, tmp_path):
        """Test merge with validation file."""
        template = tmp_path / "template.txt"
        template.write_text("Hello World")
        
        validate = tmp_path / "validate.txt"
        validate.write_text("Hello World")
        
        result, diff = merge(
            template=str(template),
            validate=str(validate)
        )
        
        assert result == "Hello World"
        assert diff == ""  # No difference

    def test_merge_output_to_file(self, tmp_path):
        """Test merge outputs to file."""
        template = tmp_path / "template.txt"
        template.write_text("Content")
        
        output = tmp_path / "output.txt"
        
        merge(
            template=str(template),
            output=str(output)
        )
        
        assert output.read_text() == "Content"

    def test_merge_config_json_output(self, tmp_path, capsys):
        """Test merge with config-json output."""
        config = tmp_path / "config.json"
        config.write_text('{"key": "value"}')
        
        merge(
            config=[str(config)],
            output="config-json"
        )
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == {"key": "value"}

    def test_merge_config_yaml_output(self, tmp_path, capsys):
        """Test merge with config-yaml output."""
        config = tmp_path / "config.json"
        config.write_text('{"key": "value"}')
        
        merge(
            config=[str(config)],
            output="config-yaml"
        )
        
        captured = capsys.readouterr()
        output = yaml.safe_load(captured.out)
        assert output == {"key": "value"}

    @pytest.mark.skip(reason="""
        Getting inconsistent results across multiple runs. 
        I suspect due to the nature of setting filters in Jinja is modifying a global function
    """)
    def test_merge_with_functions(self, tmp_path):
        """Test merge with custom functions."""
        func_file = tmp_path / "merge_with_functions" / "merge_with_functions.py"
        func_file.parent.mkdir(parents=True, exist_ok=True)
        func_file.write_text(textwrap.dedent("""
        def filter_lowercase(value):
            return value.lower()
        """))

        # Need non-empty config for Jinja templating environment to be active so that custom functions can be used.
        config = tmp_path / "merge_with_functions" / "merge_with_functions_config.json"
        config.write_text('{"name": "WORLD"}')
        
        template = tmp_path / "merge_with_functions" / "merge_with_functions_template.txt"
        template.write_text("{{ name | lowercase }}")
        
        f = get_functions([str(func_file)])
        assert "lowercase" in f["filters"]

        # The jinja2 TESTS and FILTERS dictionary is a global variable we are tweaking here.
        FILTERS.update(f["filters"])

        result, _ = merge(
            template=str(template),
            config=[str(config)],
            functions=[str(func_file)]
        )

        assert "lowercase" in FILTERS
        assert result == "world"

    @patch("sys.stdin")
    def test_merge_with_stdin(self, mock_stdin, tmp_path):
        """Test merge with stdin input."""
        mock_stdin.isatty.return_value = False
        mock_stdin.read.return_value = '{"stdin_key": "stdin_value"}'
        
        template = tmp_path / "template.txt"
        template.write_text("{{ stdin_key }}")
        
        result, _ = merge(
            template=str(template),
            stdin_format="json"
        )
        
        assert result == "stdin_value"


class TestMainFunction:
    """Test the main CLI entry point."""

    def test_main_basic(self, tmp_path):
        """Test main function with basic arguments."""
        template = tmp_path / "template.txt"
        template.write_text("Test")
        
        with patch("injinja.injinja.merge") as mock_merge:
            mock_merge.return_value = ("Test", None)
            main(["-t", str(template)])
            
            mock_merge.assert_called_once()
            call_args = mock_merge.call_args[1]
            assert call_args["template"] == str(template)

    def test_main_with_all_args(self, tmp_path):
        """Test main function with all arguments."""
        template = tmp_path / "template.txt"
        template.write_text("Test")
        
        config = tmp_path / "config.json"
        config.write_text('{"key": "value"}')
        
        with patch("injinja.injinja.merge") as mock_merge:
            mock_merge.return_value = ("Test", None)
            main([
                "-t", str(template),
                "-c", str(config),
                "-e", "KEY=VALUE",
                "-p", "PREFIX_",
                "-o", "output.txt",
                "--stdin-format", "json"
            ])
            
            mock_merge.assert_called_once()
            call_args = mock_merge.call_args[1]
            assert call_args["template"] == str(template)
            assert str(config) in call_args["config"]
            assert "KEY=VALUE" in call_args["env"]
            assert "PREFIX_" in call_args["prefix"]
            assert call_args["output"] == "output.txt"
            assert call_args["stdin_format"] == "json"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_config_list(self):
        """Test with empty configuration list."""
        result = reduce_confs([])
        assert result == {}

    def test_merge_creates_parent_directories(self, tmp_path):
        """Test merge creates parent directories for output."""
        template = tmp_path / "template.txt"
        template.write_text("Content")
        
        output = tmp_path / "nested" / "dir" / "output.txt"
        
        merge(
            template=str(template),
            output=str(output)
        )
        
        assert output.exists()
        assert output.read_text() == "Content"

    def test_expand_files_list(self, tmp_path):
        """Test expand files list."""
        
        pwd = pathlib.Path.cwd()
        relative_tmp_path = (pwd / "tmp").relative_to(pwd)
        temp_file_1 = relative_tmp_path / "expand_files_list" / "_expand_files_list_1.txt"
        temp_file_1.parent.mkdir(parents=True, exist_ok=True)
        temp_file_1.write_text("Content")
        
        temp_file_2 = relative_tmp_path / "expand_files_list" / "_expand_files_list_2.txt"
        temp_file_2.write_text("Content")

        glob_path_str = str(relative_tmp_path / "expand_files_list") + "/*.txt"

        result = expand_files_list(glob_path_str)
        shutil.rmtree(relative_tmp_path / "expand_files_list")
        assert result == [str(temp_file_1), str(temp_file_2)]