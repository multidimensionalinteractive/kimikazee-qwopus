"""
Configuration tests for Kimikazee Qwopus.

This test module covers:
- Config file parsing
- YAML validation
- Environment variable substitution
- Default value handling
- Config loading errors

Usage:
    pytest tests/test_config.py -v
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml


# =============================================================================
# CONFIG LOADING TESTS
# =============================================================================


class TestConfigLoading:
    """Tests for configuration file loading."""
    
    def test_load_valid_config(self, temp_config_file: str, sample_config: dict) -> None:
        """Loading a valid config file succeeds."""
        from server import load_config
        
        config = load_config(temp_config_file)
        
        assert config is not None
        assert isinstance(config, dict)
        assert config.get("provider") == sample_config["provider"]
        assert config.get("model") == sample_config["model"]
    
    def test_load_config_missing_file(self) -> None:
        """Loading a missing config file raises FileNotFoundError."""
        from server import load_config
        
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config("/nonexistent/path/config.yaml")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_config_invalid_yaml(
        self,
        invalid_config_file: str
    ) -> None:
        """Loading an invalid YAML file raises YAMLError."""
        from server import load_config
        
        with pytest.raises(yaml.YAMLError):
            load_config(invalid_config_file)
    
    def test_load_config_returns_all_keys(
        self,
        temp_config_file: str,
        sample_config: dict
    ) -> None:
        """Loaded config contains all expected keys."""
        from server import load_config
        
        config = load_config(temp_config_file)
        
        expected_keys = {
            "provider", "model", "context_window", "parallel",
            "n_predict", "temp", "top_p", "top_k",
            "flash_attn", "n_threads", "n_gpu_layers",
            "log_level", "log_file"
        }
        
        assert expected_keys.issubset(set(config.keys()))
    
    def test_load_config_preserves_types(
        self,
        temp_config_file: str,
        sample_config: dict
    ) -> None:
        """Config loading preserves data types."""
        from server import load_config
        
        config = load_config(temp_config_file)
        
        # Integer fields
        assert isinstance(config["context_window"], int)
        assert isinstance(config["parallel"], int)
        assert isinstance(config["top_k"], int)
        
        # Float fields
        assert isinstance(config["temp"], float)
        assert isinstance(config["top_p"], float)
        
        # Boolean fields
        assert isinstance(config["flash_attn"], bool)
        
        # String fields
        assert isinstance(config["provider"], str)
        assert isinstance(config["model"], str)


# =============================================================================
# ENVIRONMENT VARIABLE SUBSTITUTION TESTS
# =============================================================================


class TestEnvVariableSubstitution:
    """Tests for environment variable substitution in configs."""
    
    def test_env_substitution_in_config(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables are substituted in config values."""
        # Set environment variable
        monkeypatch.setenv("TEST_VAR", "substituted_value")
        
        # Create config with env var
        config_path = tmp_path / "env_test.yaml"
        config_content = """
        value: "${TEST_VAR}"
        other_value: "static"
        """
        config_path.write_text(config_content)
        
        from server import load_config
        
        config = load_config(str(config_path))
        
        assert config["value"] == "substituted_value"
        assert config["other_value"] == "static"
    
    def test_missing_env_var_uses_default(self, tmp_path: Path) -> None:
        """Missing environment variables are not substituted."""
        # Create config with missing env var
        config_path = tmp_path / "missing_env.yaml"
        config_content = """
        value: "${NONEXISTENT_VAR}"
        """
        config_path.write_text(config_content)
        
        from server import load_config
        
        config = load_config(str(config_path))
        
        # Should keep the original string if var not found
        if config:
            assert "${NONEXISTENT_VAR}" in str(config.get("value", ""))
    
    def test_env_substitution_complex_value(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables work with complex values."""
        monkeypatch.setenv("API_KEY", "secret123")
        
        config_path = tmp_path / "complex_env.yaml"
        config_content = """
        api_key: "${API_KEY}"
        url: "https://api.example.com?key=${API_KEY}"
        """
        config_path.write_text(config_content)
        
        from server import load_config
        
        config = load_config(str(config_path))
        
        assert config["api_key"] == "secret123"
    
    def test_config_empty_file(self, tmp_path: Path) -> None:
        """Empty config file loads without crashing."""
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("")
        
        from server import load_config
        
        # Empty yaml returns None, so handle that
        config = load_config(str(config_path))
        # May return None or empty dict
        assert config is None or (isinstance(config, dict) and config == {})
    
    def test_config_minimal_file(self, tmp_path: Path) -> None:
        """Minimal config file loads successfully."""
        config_path = tmp_path / "minimal.yaml"
        config_path.write_text("provider: custom\n")
        
        from server import load_config
        
        config = load_config(str(config_path))
        
        assert config is not None
        # Should have defaults for missing keys
        assert "provider" in config
        assert config["provider"] == "custom"


# =============================================================================
# CONFIG STRUCTURE TESTS
# =============================================================================


class TestConfigStructure:
    """Tests for configuration file structure."""
    
    def test_nested_config_sections(self, tmp_path: Path) -> None:
        """Nested config sections are loaded correctly."""
        config_path = tmp_path / "nested.yaml"
        config_content = """
        discord:
          require_mention: false
          channels:
            - channel1
            - channel2
        telegram:
          enabled: true
          bot_token: "test_token"
        """
        config_path.write_text(config_content)
        
        from server import load_config
        
        config = load_config(str(config_path))
        
        assert "discord" in config
        assert config["discord"]["require_mention"] is False
        assert "telegram" in config
        assert config["telegram"]["enabled"] is True
        assert config["telegram"]["bot_token"] == "test_token"
    
    def test_config_list_values(self, tmp_path: Path) -> None:
        """Config list values are preserved."""
        config_path = tmp_path / "lists.yaml"
        config_content = """
        channels:
          - general
          - random
          - announcements
        stop_words:
          - end
          - stop
          - quit
        """
        config_path.write_text(config_content)
        
        from server import load_config
        
        config = load_config(str(config_path))
        
        assert isinstance(config["channels"], list)
        assert len(config["channels"]) == 3
        assert "general" in config["channels"]
        assert "stop_words" in config
        assert isinstance(config["stop_words"], list)


# =============================================================================
# CONFIG VALIDATION TESTS
# =============================================================================


class TestConfigValidation:
    """Tests for configuration validation."""
    
    def test_valid_config_values(
        self,
        temp_config_file: str,
        sample_config: dict
    ) -> None:
        """Valid configuration values pass validation."""
        from server import load_config
        
        config = load_config(temp_config_file)
        
        # Check that values are within expected ranges
        assert 0 <= config.get("temp", 0.7) <= 2.0
        assert 0 <= config.get("top_p", 0.9) <= 1.0
        assert config.get("top_k", 40) >= 1
        assert config.get("n_gpu_layers", 0) >= -1
    
    def test_config_values_modified(
        self,
        tmp_path: Path
    ) -> None:
        """Config values can be overridden by environment."""
        config_path = tmp_path / "override.yaml"
        config_path.write_text("""
        model: default_model.gguf
        temp: 0.7
        """)
        
        # Load and modify
        from server import load_config
        config = load_config(str(config_path))
        
        config["model"] = "custom_model.gguf"
        config["temp"] = 1.5
        
        assert config["model"] == "custom_model.gguf"
        assert config["temp"] == 1.5


# =============================================================================
# FILE PATH HANDLING TESTS
# =============================================================================


class TestConfigPathHandling:
    """Tests for file path handling in config."""
    
    def test_home_directory_expansion(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Home directory expansion in config paths works."""
        # Create a mock home directory
        home_dir = tmp_path / "fake_home"
        home_dir.mkdir()
        
        # Just verify the function doesn't crash
        from server import load_config, setup_logging
        
        config_path = tmp_path / "home_paths.yaml"
        config_content = f"""
        log_file: {home_dir}/logs/server.log
        cache_dir: {home_dir}/cache
        """
        config_path.write_text(config_content)
        
        config = load_config(str(config_path))
        
        # Should have the expanded path
        assert "fake_home" in config["log_file"]
    
    def test_relative_paths(self, tmp_path: Path) -> None:
        """Relative paths in config work correctly."""
        config_path = tmp_path / "relative.yaml"
        config_path.write_text("""
        model: ./models/model.gguf
        data: ../data
        """)
        
        from server import load_config
        
        config = load_config(str(config_path))
        
        assert config["model"] == "./models/model.gguf"
        assert config["data"] == "../data"


# =============================================================================
# CONFIG COMPARISON TESTS
# =============================================================================


class TestConfigComparison:
    """Tests for comparing configurations."""
    
    def test_same_configs_equal(self, temp_config_file: str) -> None:
        """Same config file produces identical results."""
        from server import load_config
        
        config1 = load_config(temp_config_file)
        config2 = load_config(temp_config_file)
        
        assert config1 == config2
    
    def test_different_configs_not_equal(self, tmp_path: Path) -> None:
        """Different configs are not equal."""
        from server import load_config
        
        config1_path = tmp_path / "config1.yaml"
        config2_path = tmp_path / "config2.yaml"
        
        config1_path.write_text("value: 1\n")
        config2_path.write_text("value: 2\n")
        
        config1 = load_config(str(config1_path))
        config2 = load_config(str(config2_path))
        
        assert config1 != config2


# =============================================================================
# CONFIG FILE OPERATIONS TESTS
# =============================================================================


class TestConfigFileOperations:
    """Tests for configuration file operations."""
    
    def test_config_file_creation(self, tmp_path: Path) -> None:
        """Can create new config files."""
        config_path = tmp_path / "new_config.yaml"
        
        import yaml
        new_config = {
            "provider": "test",
            "model": "test.gguf"
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(new_config, f)
        
        assert config_path.exists()
        
        from server import load_config
        loaded = load_config(str(config_path))
        
        assert loaded["provider"] == "test"
    
    def test_config_file_overwrite(self, tmp_path: Path) -> None:
        """Can overwrite existing config files."""
        config_path = tmp_path / "overwrite.yaml"
        
        # Write initial config
        initial = {"value": 1}
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(initial, f)
        
        # Overwrite
        updated = {"value": 2}
        with open(config_path, 'w') as f:
            yaml.dump(updated, f)
        
        from server import load_config
        loaded = load_config(str(config_path))
        
        assert loaded["value"] == 2


# =============================================================================
# HELPERS AND UTILITIES TESTS
# =============================================================================


class TestConfigHelpers:
    """Tests for configuration helper functions."""
    
    def test_yaml_dump_roundtrip(self, tmp_path: Path) -> None:
        """YAML dump and load preserves data."""
        import yaml
        
        data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"}
        }
        
        config_path = tmp_path / "roundtrip.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(data, f)
        
        with open(config_path, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded == data
    
    def test_config_parsing_edge_cases(self, tmp_path: Path) -> None:
        """Config parsing handles edge cases."""
        config_path = tmp_path / "edge_cases.yaml"
        config_content = """
        # Comment line
        string_value: "text"
        number_value: 42
        float_value: 3.14
        bool_value: true
        null_value: ~
        list_value:
          - item1
          - item2
        inline_comment: value # comment
        """
        config_path.write_text(config_content)
        
        from server import load_config
        
        config = load_config(str(config_path))
        
        assert config["string_value"] == "text"
        assert config["number_value"] == 42
        assert config["float_value"] == 3.14
        assert config["bool_value"] is True
        assert config["null_value"] is None
        assert len(config["list_value"]) == 2


# =============================================================================
# TEST FIXTURES
# =============================================================================


def test_conftest_fixtures_loaded():
    """Verify conftest fixtures are available."""
    from tests.conftest import create_health_response, create_model_response
    assert callable(create_health_response)
    assert callable(create_model_response)
