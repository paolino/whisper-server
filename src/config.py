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

    model_config = {"env_prefix": "WHISPER_"}


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config()
