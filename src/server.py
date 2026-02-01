"""WebSocket server implementing Konele protocol."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

import websockets
from aiohttp import web
from websockets.http11 import Request, Response

if TYPE_CHECKING:
    from websockets.asyncio.server import ServerConnection

from config import Config, load_config
from postprocessor import PostProcessor
from transcriber import Transcriber

SUPPORTED_AUDIO_EXTENSIONS = {".oga", ".ogg", ".wav", ".mp3", ".m4a"}


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
        self.postprocessor = PostProcessor(config)

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

        if self.postprocessor.enabled:
            transcript = await loop.run_in_executor(
                None,
                self.postprocessor.process,
                transcript,
                self.config.language,
            )
            logger.info("Post-processed: %s", transcript)

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

    async def handle_transcribe(self, request: web.Request) -> web.Response:
        """Handle HTTP POST /transcribe for batch transcription."""
        try:
            reader = await request.multipart()
            field = await reader.next()

            if field is None:
                return web.json_response(
                    {"error": "Missing 'audio' field in form data"},
                    status=400,
                )

            # Ensure we have a body part, not a nested multipart reader
            if not hasattr(field, "name") or field.name != "audio":
                return web.json_response(
                    {"error": "Missing 'audio' field in form data"},
                    status=400,
                )

            filename = getattr(field, "filename", None) or "audio.bin"
            extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

            if f".{extension}" not in SUPPORTED_AUDIO_EXTENSIONS:
                return web.json_response(
                    {
                        "error": f"Unsupported format '.{extension}'. "
                        f"Supported: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
                    },
                    status=400,
                )

            audio_data = await field.read()  # type: ignore[union-attr]

            if not audio_data:
                return web.json_response(
                    {"error": "Empty audio file"},
                    status=400,
                )

            logger.info(
                "HTTP transcribe: %s (%d bytes)",
                filename,
                len(audio_data),
            )

            transcript = await self.transcriber.transcribe_file(audio_data, filename)

            if self.postprocessor.enabled:
                loop = asyncio.get_event_loop()
                transcript = await loop.run_in_executor(
                    None,
                    self.postprocessor.process,
                    transcript,
                    self.config.language,
                )
                logger.info("Post-processed: %s", transcript)

            logger.info("Transcription: %s", transcript)

            return web.json_response({"text": transcript})

        except TimeoutError:
            return web.json_response(
                {"error": "Transcription timed out"},
                status=504,
            )
        except ValueError as e:
            return web.json_response(
                {"error": str(e)},
                status=400,
            )
        except Exception:
            logger.exception("Error processing transcription request")
            return web.json_response(
                {"error": "Internal server error"},
                status=500,
            )

    def _create_http_app(self) -> web.Application:
        """Create the aiohttp application for HTTP endpoints."""
        app = web.Application()
        app.router.add_post("/transcribe", self.handle_transcribe)
        return app

    async def run(self) -> None:
        """Start the WebSocket and HTTP servers."""
        logger.info("Loading Whisper model: %s", self.config.model)
        _ = self.transcriber.model  # Preload model

        if self.postprocessor.enabled:
            logger.info("Loading LLama model: %s", self.config.llama_model_path)
            _ = self.postprocessor.model  # Preload model

        logger.info(
            "Starting WebSocket server on %s:%d",
            self.config.host,
            self.config.port,
        )
        logger.info(
            "Starting HTTP server on %s:%d",
            self.config.host,
            self.config.http_port,
        )

        # Start HTTP server
        http_app = self._create_http_app()
        http_runner = web.AppRunner(http_app)
        await http_runner.setup()
        http_site = web.TCPSite(http_runner, self.config.host, self.config.http_port)
        await http_site.start()

        # Start WebSocket server
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
