"""Tests for configuration merging functions."""

# Our Libraries
from injinja.injinja import map_env_to_confs, reduce_confs


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
        confs = [{"key1": "value1", "shared": "first"}, {"key2": "value2", "shared": "second"}]

        result = reduce_confs(confs)
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert result["shared"] == "second"  # Later configs override
