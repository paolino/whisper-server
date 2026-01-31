# shellcheck shell=bash

set unstable := true

# List available recipes
default:
    @just --list

# Format all source files
format:
    #!/usr/bin/env bash
    set -euo pipefail
    black src
    ruff check --fix src

# Run linter and type checker
lint:
    #!/usr/bin/env bash
    set -euo pipefail
    ruff check src
    mypy src

# Run the whisper server
run port="9002" model="base":
    #!/usr/bin/env bash
    set -euo pipefail
    export WHISPER_PORT="{{ port }}"
    export WHISPER_MODEL="{{ model }}"
    python src/server.py

# Run tests
test:
    #!/usr/bin/env bash
    set -euo pipefail
    pytest src -v

# Full CI pipeline
CI:
    #!/usr/bin/env bash
    set -euo pipefail
    just format
    just lint
    just test

# Build docker image
build-docker tag='latest':
    #!/usr/bin/env bash
    set -euo pipefail
    nix build .#docker-image
    docker load < result
    system=$(nix eval --raw --impure --expr 'builtins.currentSystem')
    version=$(nix eval --raw ".#version.$system")
    docker image tag "ghcr.io/paolino/whisper-server:$version" \
        "ghcr.io/paolino/whisper-server:{{ tag }}"

# Start docker container
start-docker port="9002" model="base":
    #!/usr/bin/env bash
    set -euo pipefail
    docker run -d --rm \
        --name whisper-server \
        -p {{ port }}:9002 \
        -e WHISPER_MODEL="{{ model }}" \
        ghcr.io/paolino/whisper-server:latest

# Stop docker container
stop-docker:
    #!/usr/bin/env bash
    docker stop whisper-server || true

# Start with docker-compose
up:
    #!/usr/bin/env bash
    set -euo pipefail
    docker compose up -d

# Stop docker-compose
down:
    #!/usr/bin/env bash
    docker compose down

# View docker-compose logs
logs:
    #!/usr/bin/env bash
    docker compose logs -f

# Smoke test docker image
smoke-test-docker port="9003":
    #!/usr/bin/env bash
    set -euo pipefail
    just build-docker
    docker rm -f whisper-smoke 2>/dev/null || true
    docker run -d --name whisper-smoke -p {{ port }}:9002 \
        ghcr.io/paolino/whisper-server:latest
    echo "Waiting for server to start..."
    sleep 30
    nix develop --quiet --command python3 scripts/smoke-test.py {{ port }}
    docker rm -f whisper-smoke

# Serve documentation locally
serve-docs:
    #!/usr/bin/env bash
    set -euo pipefail
    nix develop github:paolino/dev-assets?dir=mkdocs -c mkdocs serve

# Build documentation
build-docs:
    #!/usr/bin/env bash
    set -euo pipefail
    nix develop github:paolino/dev-assets?dir=mkdocs -c mkdocs build

# Build cloud NixOS configuration
build-cloud target:
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{ target }}" in
        hetzner|aws|gcp)
            nix build ".#nixosConfigurations.whisper-{{ target }}.config.system.build.toplevel"
            ;;
        *)
            echo "Unknown target: {{ target }}"
            echo "Valid targets: hetzner, aws, gcp"
            exit 1
            ;;
    esac

# Deploy to Hetzner via nixos-rebuild
deploy-hetzner host:
    #!/usr/bin/env bash
    set -euo pipefail
    nixos-rebuild switch --flake ".#whisper-hetzner" \
        --target-host "root@{{ host }}" \
        --build-host "root@{{ host }}"

# Build AWS AMI
build-aws-ami:
    #!/usr/bin/env bash
    set -euo pipefail
    nix build ".#nixosConfigurations.whisper-aws.config.system.build.amazonImage"
    echo "AMI image built: $(readlink -f result)"

# Build GCP image
build-gcp-image:
    #!/usr/bin/env bash
    set -euo pipefail
    nix build ".#nixosConfigurations.whisper-gcp.config.system.build.googleComputeImage"
    echo "GCP image built: $(readlink -f result)"
