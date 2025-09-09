"""Tests for edge cases and error conditions."""

# Standard Library
import pathlib
import shutil

# Our Libraries
from injinja.injinja import (
    ConfigSchemaValidationError,
    expand_files_list,
    merge,
    reduce_confs,
)


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

        merge(template=str(template), output=str(output))

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

        result = sorted(expand_files_list(glob_path_str))
        shutil.rmtree(relative_tmp_path / "expand_files_list")
        assert result == sorted([str(temp_file_1), str(temp_file_2)])

    def test_error_handling_edge_cases(self):
        """Test error handling edge cases to improve coverage."""
        # Test ConfigSchemaValidationError with different message types
        error1 = ConfigSchemaValidationError("Simple message")
        assert str(error1) == "Simple message"

        error2 = ConfigSchemaValidationError("")  # Empty message
        assert str(error2) == ""

        # Test multiple error instantiation
        errors = [ConfigSchemaValidationError(f"Error {i}") for i in range(3)]
        assert len(errors) == 3
        assert all(isinstance(e, ConfigSchemaValidationError) for e in errors)

