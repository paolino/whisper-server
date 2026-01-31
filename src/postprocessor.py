"""LLama-based grammar and spelling correction post-processor."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llama_cpp import Llama

from config import Config

logger = logging.getLogger(__name__)

# Language-specific prompts for grammar correction
PROMPTS = {
    "en": (
        "Fix any grammar and spelling errors in the following text. "
        "Return only the corrected text without explanations:\n\n{text}"
    ),
    "it": (
        "Correggi eventuali errori grammaticali e ortografici nel seguente testo. "
        "Restituisci solo il testo corretto senza spiegazioni:\n\n{text}"
    ),
}

DEFAULT_PROMPT = PROMPTS["en"]


class PostProcessor:
    """LLama-based post-processor for grammar and spelling correction."""

    def __init__(self, config: Config) -> None:
        """Initialize the post-processor with configuration."""
        self.config = config
        self._model: Llama | None = None
        self._enabled = config.llama_enabled and config.llama_model_path is not None

    @property
    def enabled(self) -> bool:
        """Check if post-processing is enabled."""
        return self._enabled

    @property
    def model(self) -> Llama:
        """Lazy-load the LLama model."""
        if self._model is None:
            from llama_cpp import Llama

            if not self.config.llama_model_path:
                raise ValueError("LLAMA_MODEL_PATH must be set when LLama is enabled")

            logger.info("Loading LLama model from %s", self.config.llama_model_path)
            self._model = Llama(
                model_path=self.config.llama_model_path,
                n_ctx=self.config.llama_context_size,
                n_threads=self.config.llama_threads,
                verbose=False,
            )
        return self._model

    def process(self, text: str, language: str | None = None) -> str:
        """Apply grammar and spelling correction to text.

        Args:
            text: The transcribed text to correct
            language: Language code (e.g., 'en', 'it'). Defaults to English.

        Returns:
            Corrected text, or original text if correction fails
        """
        if not self._enabled:
            return text

        if not text or not text.strip():
            return text

        try:
            prompt_template = PROMPTS.get(language or "en", DEFAULT_PROMPT)
            prompt = prompt_template.format(text=text)

            response = self.model(
                prompt,
                max_tokens=self.config.llama_max_tokens,
                stop=["\n\n"],
                echo=False,
            )

            corrected: str = response["choices"][0]["text"].strip()

            if corrected:
                logger.debug("Corrected: '%s' -> '%s'", text, corrected)
                return corrected

            return text

        except Exception:
            logger.exception("LLama post-processing failed, returning raw text")
            return text
