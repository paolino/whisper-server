#!/usr/bin/env python3
"""Smoke test for whisper-server WebSocket connection."""

import asyncio
import json
import sys

import websockets


async def test(port: int) -> None:
    """Test WebSocket connection and basic response."""
    url = f"ws://localhost:{port}"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"eof": True}))
        response = await ws.recv()
        result = json.loads(response)
        assert result["status"] == 0, f"Bad status: {result}"
        assert result["result"]["final"] is True, f"Not final: {result}"
        print("SMOKE TEST PASSED")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9003
    asyncio.run(test(port))
