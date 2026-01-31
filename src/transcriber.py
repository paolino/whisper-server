"""Whisper transcription wrapper."""

import io
import struct
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

from config import Config


class Transcriber:
    """Wrapper around faster-whisper for audio transcription."""

    def __init__(self, config: Config) -> None:
        """Initialize the transcriber with configuration."""
        self.config = config
        self._model: "WhisperModel | None" = None

    @property
    def model(self) -> "WhisperModel":
        """Lazy-load the Whisper model."""
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.config.model,
                device=self.config.device,
                compute_type=self.config.compute_type,
            )
        return self._model

    def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe raw PCM audio data.

        Args:
            audio_data: Raw PCM audio (16kHz, 16-bit signed LE, mono)

        Returns:
            Transcribed text
        """
        wav_data = self._wrap_pcm_as_wav(audio_data)
        audio_array = self._wav_to_array(wav_data)

        segments, _ = self.model.transcribe(
            audio_array,
            language=self.config.language,
            vad_filter=True,
        )

        return " ".join(segment.text.strip() for segment in segments)

    def _wrap_pcm_as_wav(self, pcm_data: bytes) -> bytes:
        """Wrap raw PCM data in a WAV header."""
        sample_rate = 16000
        bits_per_sample = 16
        num_channels = 1
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_data)

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,
            1,  # PCM format
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b"data",
            data_size,
        )

        return header + pcm_data

    def _wav_to_array(self, wav_data: bytes) -> np.ndarray[np.floating]:
        """Convert WAV bytes to numpy array normalized to [-1, 1]."""
        buffer = io.BytesIO(wav_data)
        buffer.seek(44)  # Skip WAV header

        audio = np.frombuffer(buffer.read(), dtype=np.int16)
        return audio.astype(np.float32) / 32768.0
