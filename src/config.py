"""Configuration management for Whisper Server."""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Server configuration loaded from environment variables."""

    host: str = "0.0.0.0"
    port: int = 9002
    model: str = "base"
    device: str = "auto"
    compute_type: str = "auto"
    language: str | None = None

    # LLama post-processing settings
    llama_enabled: bool = False
    llama_model_path: str | None = None
    llama_context_size: int = 2048
    llama_max_tokens: int = 512
    llama_threads: int = 4

    model_config = {"env_prefix": "WHISPER_"}


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config()
