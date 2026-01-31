# Installation

This guide covers installing and running the Whisper Server on NixOS with Tailscale for secure remote access.

## Prerequisites

- NixOS system (or any Linux with Nix installed)
- Tailscale for secure network access
- GPU recommended for faster transcription (CPU works but is slower)

## Tailscale Setup

Install and configure Tailscale on your NixOS system:

```nix
# configuration.nix
{
  services.tailscale.enable = true;
}
```

After rebuilding, authenticate:

```bash
sudo tailscale up
```

Note your Tailscale IP:

```bash
tailscale ip -4
# Example: 100.64.1.42
```

## Running Manually

Clone the repository and start the server:

```bash
git clone https://github.com/paolino/whisper-server
cd whisper-server

# Enter development shell (installs faster-whisper automatically)
nix develop

# Run the server
just run
```

The server starts on port 9002 by default.

## Systemd Service

For production, create a systemd service:

```nix
# configuration.nix
{
  systemd.services.whisper-server = {
    description = "Whisper Speech-to-Text Server";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      User = "whisper";
      Group = "whisper";
      WorkingDirectory = "/opt/whisper-server";
      ExecStart = "${pkgs.bash}/bin/bash -c 'source .venv/bin/activate && python src/server.py'";
      Restart = "always";
      RestartSec = 10;

      # Security hardening
      NoNewPrivileges = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      PrivateTmp = true;
    };

    environment = {
      WHISPER_HOST = "0.0.0.0";
      WHISPER_PORT = "9002";
      WHISPER_MODEL = "base";
    };
  };

  users.users.whisper = {
    isSystemUser = true;
    group = "whisper";
    home = "/opt/whisper-server";
  };
  users.groups.whisper = {};
}
```

## Docker Deployment

Build and run with Docker:

```bash
# Build the image
just build-docker

# Start the container
just start-docker 9002 base

# Stop
just stop-docker
```

Or run directly:

```bash
docker run -d --rm \
    --name whisper-server \
    -p 9002:9002 \
    -e WHISPER_MODEL=base \
    ghcr.io/paolino/whisper-server:latest
```

## Firewall Configuration

Only expose the server on the Tailscale interface:

```nix
# configuration.nix
{
  networking.firewall = {
    enable = true;
    interfaces."tailscale0" = {
      allowedTCPPorts = [ 9002 ];
    };
  };
}
```

This ensures the server is only accessible via Tailscale, not from the public internet.

## Verifying the Installation

Test the server with a simple WebSocket client:

```python
import asyncio
import websockets
import json

async def test():
    async with websockets.connect("ws://localhost:9002") as ws:
        # Send empty audio + EOF
        await ws.send(json.dumps({"eof": True}))
        response = await ws.recv()
        print(response)

asyncio.run(test())
```

Expected output:

```json
{"status": 0, "result": {"hypotheses": [{"transcript": ""}], "final": true}}
```

## Next Steps

- [Android Setup](android-setup.md) - Configure Konele on your phone
- [Configuration](configuration.md) - Customize server options
