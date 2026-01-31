"""Tests for configuration module."""

from config import Config, load_config


def test_config_defaults() -> None:
    """Test default configuration values."""
    config = Config()
    assert config.host == "0.0.0.0"
    assert config.port == 9002
    assert config.model == "base"
    assert config.device == "auto"
    assert config.compute_type == "auto"
    assert config.language is None


def test_load_config() -> None:
    """Test load_config returns Config instance."""
    config = load_config()
    assert isinstance(config, Config)
