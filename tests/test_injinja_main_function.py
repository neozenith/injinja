"""Tests for the main CLI entry point."""

# Standard Library
from unittest.mock import patch

# Our Libraries
from injinja.injinja import main


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
            main(
                [
                    "-t",
                    str(template),
                    "-c",
                    str(config),
                    "-e",
                    "KEY=VALUE",
                    "-p",
                    "PREFIX_",
                    "-o",
                    "output.txt",
                    "--stdin-format",
                    "json",
                ]
            )

            mock_merge.assert_called_once()
            call_args = mock_merge.call_args[1]
            assert call_args["template"] == str(template)
            assert str(config) in call_args["config"]
            assert "KEY=VALUE" in call_args["env"]
            assert "PREFIX_" in call_args["prefix"]
            assert call_args["output"] == "output.txt"
            assert call_args["stdin_format"] == "json"
