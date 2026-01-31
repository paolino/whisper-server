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

## NixOS Module

The recommended way to deploy on NixOS is using the provided module:

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    whisper-server.url = "github:paolino/whisper-server";
  };

  outputs = { nixpkgs, whisper-server, ... }: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        whisper-server.nixosModules.default
        ./configuration.nix
      ];
    };
  };
}
```

Then enable the service:

```nix
# configuration.nix
{ pkgs, ... }:
{
  services.whisper-server = {
    enable = true;
    package = pkgs.fetchFromGitHub {
      owner = "paolino";
      repo = "whisper-server";
      rev = "main";
      hash = "sha256-...";
    } + "/src";
    model = "base";
    port = 9002;
  };
}
```

### Tailscale Integration

For secure remote access, enable Tailscale mode:

```nix
{
  services.whisper-server = {
    enable = true;
    package = ./path/to/whisper-server/src;
    model = "medium";
    tailscale.enable = true;
  };

  services.tailscale.enable = true;
}
```

This automatically:

- Binds to your Tailscale IP
- Opens port 9002 only on the Tailscale interface
- Starts after tailscaled

### Available Options

| Option | Default | Description |
|--------|---------|-------------|
| `enable` | `false` | Enable the service |
| `package` | required | Path to src directory |
| `host` | `"127.0.0.1"` | Listen address |
| `port` | `9002` | Listen port |
| `model` | `"base"` | Whisper model (tiny/base/small/medium/large-v3) |
| `device` | `"auto"` | Compute device (auto/cpu/cuda) |
| `computeType` | `"auto"` | Precision (auto/int8/float16/float32) |
| `language` | `null` | Language code (null for auto-detect) |
| `tailscale.enable` | `false` | Listen on Tailscale only |
| `tailscale.interface` | `"tailscale0"` | Tailscale interface name |

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

When using `tailscale.enable = true`, the firewall is configured automatically.

For manual setups, only expose the server on the Tailscale interface:

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

Run the smoke test:

```bash
nix run github:paolino/whisper-server#smoke-test -- 9002
```

Or if you have the repo cloned:

```bash
nix run .#smoke-test -- 9002
```

Expected output:

```
SMOKE TEST PASSED
```

## Next Steps

- [Android Setup](android-setup.md) - Configure Konele on your phone
- [Configuration](configuration.md) - Customize server options
