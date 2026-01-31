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
