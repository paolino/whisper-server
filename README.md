# Whisper Server

Self-hosted Whisper speech-to-text server compatible with [Konele](https://kaljurand.github.io/K6nele/) Android app.

## Features

- WebSocket server implementing Konele protocol
- Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- Nix flake for reproducible builds
- Docker image for easy deployment
- NixOS module for systemd integration

## Quick Start

```bash
# Enter development shell
nix develop

# Run the server
just run

# Or with custom port and model
just run 9002 medium
```

## Documentation

Full documentation available at [paolino.github.io/whisper-server](https://paolino.github.io/whisper-server/)

## License

MIT
