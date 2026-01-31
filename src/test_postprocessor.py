"""Tests for postprocessor module."""

from unittest.mock import MagicMock

from config import Config
from postprocessor import PROMPTS, PostProcessor


def test_postprocessor_disabled_by_default() -> None:
    """Post-processor should be disabled by default."""
    config = Config()
    processor = PostProcessor(config)
    assert not processor.enabled


def test_postprocessor_disabled_without_model_path() -> None:
    """Post-processor should be disabled without model path."""
    config = Config(llama_enabled=True)
    processor = PostProcessor(config)
    assert not processor.enabled


def test_postprocessor_enabled_with_config() -> None:
    """Post-processor should be enabled with proper config."""
    config = Config(llama_enabled=True, llama_model_path="/path/to/model.gguf")
    processor = PostProcessor(config)
    assert processor.enabled


def test_process_returns_text_when_disabled() -> None:
    """Process should return original text when disabled."""
    config = Config()
    processor = PostProcessor(config)
    text = "hello world"
    assert processor.process(text) == text


def test_process_returns_empty_string_unchanged() -> None:
    """Process should return empty strings unchanged."""
    config = Config(llama_enabled=True, llama_model_path="/path/to/model.gguf")
    processor = PostProcessor(config)
    processor._enabled = False  # Force disabled for this test
    assert processor.process("") == ""
    assert processor.process("   ") == "   "


def test_prompts_available() -> None:
    """Check that prompts are defined for supported languages."""
    assert "en" in PROMPTS
    assert "it" in PROMPTS
    assert "{text}" in PROMPTS["en"]
    assert "{text}" in PROMPTS["it"]


def test_process_calls_llama() -> None:
    """Process should call LLama model when enabled."""
    mock_model = MagicMock()
    mock_model.return_value = {"choices": [{"text": "corrected text"}]}

    config = Config(llama_enabled=True, llama_model_path="/path/to/model.gguf")
    processor = PostProcessor(config)
    processor._model = mock_model

    result = processor.process("original text")

    assert result == "corrected text"
    mock_model.assert_called_once()


def test_process_handles_llama_error() -> None:
    """Process should return original text on LLama error."""
    mock_model = MagicMock()
    mock_model.side_effect = RuntimeError("Model error")

    config = Config(llama_enabled=True, llama_model_path="/path/to/model.gguf")
    processor = PostProcessor(config)
    processor._model = mock_model

    result = processor.process("original text")

    assert result == "original text"


def test_process_uses_language_prompt() -> None:
    """Process should use language-specific prompt."""
    mock_model = MagicMock()
    mock_model.return_value = {"choices": [{"text": "testo corretto"}]}

    config = Config(llama_enabled=True, llama_model_path="/path/to/model.gguf")
    processor = PostProcessor(config)
    processor._model = mock_model

    processor.process("testo originale", language="it")

    call_args = mock_model.call_args
    prompt = call_args[0][0]
    assert "correggendo" in prompt
