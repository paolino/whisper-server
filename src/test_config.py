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


def test_llama_config_defaults() -> None:
    """Test LLama configuration defaults."""
    config = Config()
    assert config.llama_enabled is False
    assert config.llama_model_path is None
    assert config.llama_context_size == 2048
    assert config.llama_max_tokens == 512
    assert config.llama_threads == 4


def test_llama_config_custom_values() -> None:
    """Test LLama configuration with custom values."""
    config = Config(
        llama_enabled=True,
        llama_model_path="/models/tinyllama.gguf",
        llama_context_size=4096,
        llama_max_tokens=1024,
        llama_threads=8,
    )
    assert config.llama_enabled is True
    assert config.llama_model_path == "/models/tinyllama.gguf"
    assert config.llama_context_size == 4096
    assert config.llama_max_tokens == 1024
    assert config.llama_threads == 8


def test_load_config() -> None:
    """Test load_config returns Config instance."""
    config = load_config()
    assert isinstance(config, Config)
