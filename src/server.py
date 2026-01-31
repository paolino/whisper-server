"""WebSocket server implementing Konele protocol."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

import websockets
from websockets.http11 import Request, Response

if TYPE_CHECKING:
    from websockets.asyncio.server import ServerConnection

from config import Config, load_config
from transcriber import Transcriber


def process_request(
    connection: ServerConnection,
    request: Request,
) -> Response | None:
    """Process incoming WebSocket request.

    Removes empty Sec-WebSocket-Protocol header that Konele sends,
    which would otherwise cause the websockets library to reject
    the connection.
    """
    # Remove empty subprotocol header (Konele sends this)
    if "Sec-WebSocket-Protocol" in request.headers:
        protocol = request.headers["Sec-WebSocket-Protocol"]
        if not protocol or not protocol.strip():
            del request.headers["Sec-WebSocket-Protocol"]
    return None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class WhisperServer:
    """WebSocket server for Konele speech-to-text."""

    def __init__(self, config: Config) -> None:
        """Initialize server with configuration."""
        self.config = config
        self.transcriber = Transcriber(config)

    async def handle_connection(self, websocket: ServerConnection) -> None:
        """Handle a WebSocket connection from Konele."""
        client_addr = websocket.remote_address
        logger.info("Client connected: %s", client_addr)

        audio_buffer = bytearray()

        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    audio_buffer.extend(message)
                elif isinstance(message, str):
                    await self._handle_control_message(
                        websocket,
                        message,
                        audio_buffer,
                    )
                    audio_buffer.clear()
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected: %s", client_addr)
        except Exception:
            logger.exception("Error handling connection from %s", client_addr)

    async def _handle_control_message(
        self,
        websocket: ServerConnection,
        message: str,
        audio_buffer: bytearray,
    ) -> None:
        """Handle control message from Konele.

        Supports both:
        - "EOS" string (kaldi-gstreamer-server protocol, used by Konele)
        - {"eof": true} JSON (alternative format)
        """
        # Handle Konele's EOS string
        if message == "EOS":
            await self._transcribe_and_respond(websocket, bytes(audio_buffer))
            return

        # Handle JSON format
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.warning("Unknown control message: %s", message)
            return

        if data.get("eof"):
            await self._transcribe_and_respond(websocket, bytes(audio_buffer))

    async def _transcribe_and_respond(
        self,
        websocket: ServerConnection,
        audio_data: bytes,
    ) -> None:
        """Transcribe audio and send response."""
        if not audio_data:
            await self._send_response(websocket, "", final=True)
            return

        logger.info("Transcribing %d bytes of audio", len(audio_data))

        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(
            None,
            self.transcriber.transcribe,
            audio_data,
        )

        logger.info("Transcription: %s", transcript)
        await self._send_response(websocket, transcript, final=True)

    async def _send_response(
        self,
        websocket: ServerConnection,
        transcript: str,
        final: bool = False,
    ) -> None:
        """Send response in Konele format."""
        response: dict[str, Any] = {
            "status": 0,
            "result": {
                "hypotheses": [{"transcript": transcript}],
                "final": final,
            },
        }
        await websocket.send(json.dumps(response))

    async def run(self) -> None:
        """Start the WebSocket server."""
        logger.info("Loading Whisper model: %s", self.config.model)
        _ = self.transcriber.model  # Preload model

        logger.info(
            "Starting server on %s:%d",
            self.config.host,
            self.config.port,
        )

        async with websockets.serve(
            self.handle_connection,
            self.config.host,
            self.config.port,
            process_request=process_request,
        ):
            await asyncio.Future()  # Run forever


def main() -> None:
    """Entry point for the server."""
    config = load_config()
    server = WhisperServer(config)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
