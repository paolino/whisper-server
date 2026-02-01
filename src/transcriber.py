"""Whisper transcription wrapper."""

from __future__ import annotations

import asyncio
import io
import struct
import subprocess
from pathlib import Path
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
        self._model: WhisperModel | None = None

    @property
    def model(self) -> WhisperModel:
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

    async def transcribe_file(self, audio_data: bytes, filename: str) -> str:
        """Transcribe audio from a file.

        Uses ffmpeg to convert to PCM format if needed.

        Args:
            audio_data: Raw audio file bytes
            filename: Original filename (used to determine format)

        Returns:
            Transcribed text
        """
        loop = asyncio.get_event_loop()
        pcm_data = await loop.run_in_executor(
            None,
            self._convert_to_pcm,
            audio_data,
            filename,
        )
        return await loop.run_in_executor(None, self.transcribe, pcm_data)

    def _convert_to_pcm(self, audio_data: bytes, filename: str) -> bytes:
        """Convert audio file to raw PCM using ffmpeg.

        Args:
            audio_data: Raw audio file bytes
            filename: Original filename (for format detection)

        Returns:
            Raw PCM data (16kHz, 16-bit signed LE, mono)
        """
        suffix = Path(filename).suffix.lower()

        # If already PCM-compatible WAV, try direct processing
        if suffix == ".wav":
            try:
                return self._extract_pcm_from_wav(audio_data)
            except ValueError:
                pass  # Fall through to ffmpeg conversion

        # Use ffmpeg to convert to PCM
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                "pipe:0",
                "-f",
                "s16le",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                "pipe:1",
            ],
            input=audio_data,
            capture_output=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise ValueError(f"ffmpeg conversion failed: {result.stderr.decode()}")

        return result.stdout

    def _extract_pcm_from_wav(self, wav_data: bytes) -> bytes:
        """Extract PCM data from WAV file if format is compatible.

        Args:
            wav_data: WAV file bytes

        Returns:
            Raw PCM data

        Raises:
            ValueError: If WAV format is not compatible
        """
        if len(wav_data) < 44:
            raise ValueError("WAV file too short")

        # Parse WAV header
        if wav_data[:4] != b"RIFF" or wav_data[8:12] != b"WAVE":
            raise ValueError("Not a valid WAV file")

        # Find data chunk
        pos = 12
        while pos < len(wav_data) - 8:
            chunk_id = wav_data[pos : pos + 4]
            chunk_size = struct.unpack("<I", wav_data[pos + 4 : pos + 8])[0]

            if chunk_id == b"data":
                return wav_data[pos + 8 : pos + 8 + chunk_size]

            pos += 8 + chunk_size

        raise ValueError("No data chunk found in WAV")

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

    def _wav_to_array(self, wav_data: bytes) -> np.ndarray:
        """Convert WAV bytes to numpy array normalized to [-1, 1]."""
        buffer = io.BytesIO(wav_data)
        buffer.seek(44)  # Skip WAV header

        audio = np.frombuffer(buffer.read(), dtype=np.int16)
        return audio.astype(np.float32) / 32768.0
