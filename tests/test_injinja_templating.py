"""Tests for template merging functions."""

# Third Party
import jinja2
import pytest

# Our Libraries
from injinja.injinja import merge_template


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

    def test_merge_template_undefined_error(self, tmp_path):
        """Test merge_template with undefined variables handles gracefully."""
        template_file = tmp_path / "template.txt"
        template_file.write_text("Hello {{ undefined_var }}")

        # This will raise an UndefinedError in Jinja2 v3+ since StrictUndefined is used.
        # `config` can not be False-y otherwise it gets treated as raw content.
        with pytest.raises(jinja2.exceptions.UndefinedError) as exc_info:
            _ = merge_template(str(template_file), {"name": "Taylor Swift"})

        assert "undefined_var" in str(exc_info.value)

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
