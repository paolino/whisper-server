# Configuration

The Whisper Server is configured via environment variables.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_HOST` | `0.0.0.0` | Host address to bind |
| `WHISPER_PORT` | `9002` | Port to listen on |
| `WHISPER_MODEL` | `base` | Whisper model to use |
| `WHISPER_DEVICE` | `auto` | Device: `auto`, `cpu`, `cuda` |
| `WHISPER_COMPUTE_TYPE` | `auto` | Compute type for quantization |
| `WHISPER_LANGUAGE` | (none) | Force specific language (e.g., `en`) |

## Whisper Models

Available models from smallest to largest:

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | 39M | Fastest | Basic |
| `base` | 74M | Fast | Good |
| `small` | 244M | Medium | Better |
| `medium` | 769M | Slow | Great |
| `large-v3` | 1.5G | Slowest | Best |

!!! tip "Recommendation"
    Start with `base` for a balance of speed and accuracy. Use `small` or `medium` if you need better results and have the hardware.

## Compute Types

For GPU inference, you can specify quantization:

| Type | Description |
|------|-------------|
| `auto` | Automatic selection |
| `float16` | Half precision (GPU) |
| `float32` | Full precision |
| `int8` | 8-bit quantization |
| `int8_float16` | Mixed precision |

Lower precision = faster inference but slightly reduced accuracy.

## Example Configurations

### Development (CPU)

```bash
export WHISPER_HOST=127.0.0.1
export WHISPER_PORT=9002
export WHISPER_MODEL=base
export WHISPER_DEVICE=cpu
```

### Production (GPU)

```bash
export WHISPER_HOST=0.0.0.0
export WHISPER_PORT=9002
export WHISPER_MODEL=medium
export WHISPER_DEVICE=cuda
export WHISPER_COMPUTE_TYPE=float16
```

### Specific Language

```bash
export WHISPER_LANGUAGE=en  # Force English
# or
export WHISPER_LANGUAGE=it  # Force Italian
```

When `WHISPER_LANGUAGE` is not set, the model auto-detects the language.

## Using with Just

The justfile supports port and model arguments:

```bash
# Default (port 9002, model base)
just run

# Custom port
just run 8080

# Custom port and model
just run 9002 medium

# Docker with custom settings
just start-docker 9002 small
```

## Docker Environment

Pass environment variables to Docker:

```bash
docker run -d --rm \
    --name whisper-server \
    -p 9002:9002 \
    -e WHISPER_MODEL=medium \
    -e WHISPER_DEVICE=cpu \
    -e WHISPER_LANGUAGE=en \
    ghcr.io/paolino/whisper-server:latest
```

## NixOS Configuration

In your NixOS configuration:

```nix
{
  systemd.services.whisper-server = {
    environment = {
      WHISPER_HOST = "0.0.0.0";
      WHISPER_PORT = "9002";
      WHISPER_MODEL = "medium";
      WHISPER_DEVICE = "cuda";
      WHISPER_COMPUTE_TYPE = "float16";
    };
    # ... rest of service config
  };
}
```

## Performance Tuning

### Memory Usage

Larger models require more RAM/VRAM:

| Model | RAM (CPU) | VRAM (GPU) |
|-------|-----------|------------|
| tiny | ~1GB | ~1GB |
| base | ~1GB | ~1GB |
| small | ~2GB | ~2GB |
| medium | ~5GB | ~5GB |
| large-v3 | ~10GB | ~10GB |

### First Request Latency

The model is loaded on first request. To preload at startup, the server loads the model when it starts.

### Concurrent Requests

The current implementation processes one request at a time. For multiple concurrent users, consider running multiple server instances behind a load balancer.
