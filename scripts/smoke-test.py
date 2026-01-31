#!/usr/bin/env python3
"""Smoke test for whisper-server WebSocket connection."""

import asyncio
import json
import sys

import websockets


async def test_eos(port: int, path: str = "") -> None:
    """Test with EOS string (Konele protocol)."""
    url = f"ws://localhost:{port}{path}"
    async with websockets.connect(url) as ws:
        await ws.send("EOS")
        response = await ws.recv()
        result = json.loads(response)
        assert result["status"] == 0, f"Bad status: {result}"
        assert result["result"]["final"] is True, f"Not final: {result}"


async def test_json(port: int, path: str = "") -> None:
    """Test with JSON eof (alternative protocol)."""
    url = f"ws://localhost:{port}{path}"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"eof": True}))
        response = await ws.recv()
        result = json.loads(response)
        assert result["status"] == 0, f"Bad status: {result}"
        assert result["result"]["final"] is True, f"Not final: {result}"


async def test(port: int) -> None:
    """Run all smoke tests."""
    # Test root path with both protocols
    await test_eos(port)
    print("  EOS protocol on / ... OK")

    await test_json(port)
    print("  JSON protocol on / ... OK")

    # Test kaldi-gstreamer-server path (used by Konele)
    await test_eos(port, "/client/ws/speech")
    print("  EOS protocol on /client/ws/speech ... OK")

    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9003
    asyncio.run(test(port))
