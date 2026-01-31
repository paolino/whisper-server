# CI/CD

This document describes the CI/CD workflows for building and releasing Whisper Server.

## Overview

```mermaid
graph LR
    subgraph Development
        FB[Feature Branch]
        PR[Pull Request]
    end

    subgraph main
        M[main branch]
    end

    subgraph Release
        R[Manual Trigger]
        D[Tag + Docker + GitHub Release]
        S[Summary only]
    end

    FB -->|push| PR
    PR -->|CI passes| M
    M -->|workflow_dispatch| R
    R -->|dry_run=false| D
    R -->|dry_run=true| S
```

Feature branches trigger CI on PR. After merge to main, releases are triggered manually. With `dry_run=false`, the release workflow creates a git tag, pushes the Docker image, and creates a GitHub release. With `dry_run=true`, no changes are made - only a summary is printed.

## CI Workflow

Runs automatically on every pull request and push to main:

```mermaid
graph TD
    subgraph Trigger
        PR[Pull Request]
        Push[Push to main]
    end

    subgraph "Parallel Jobs"
        Lint[lint<br/>black + ruff + mypy]
        Test[test<br/>pytest]
        Build[build-docker<br/>nix build]
    end

    subgraph Sequential
        Smoke[smoke-test<br/>Start container + verify]
    end

    PR --> Lint
    PR --> Test
    PR --> Build
    Push --> Lint
    Push --> Test
    Push --> Build
    Build --> Smoke
```

## Release Workflow

Manual workflow triggered via GitHub Actions UI:

```mermaid
graph TD
    subgraph Input
        V[version: X.Y.Z]
        D[dry_run: true/false]
    end

    subgraph Validate
        VF[Validate version format]
        TC[Check tag doesn't exist]
    end

    subgraph Test
        FMT[Format check]
        TYPE[Type check]
        UT[Unit tests]
        DB[Docker build]
    end

    subgraph Release
        UV[Update VERSION file]
        TAG[Create git tag]
        PUSH[Push to ghcr.io]
        GHR[Create GitHub Release]
    end

    subgraph "Dry Run"
        SUM[Print summary]
    end

    V --> VF
    VF --> TC
    TC --> FMT
    FMT --> TYPE
    TYPE --> UT
    UT --> DB
    DB -->|dry_run=false| UV
    DB -->|dry_run=true| SUM
    UV --> TAG
    TAG --> PUSH
    PUSH --> GHR
```

## Triggering a Release

1. Go to **Actions** > **Release** workflow
2. Click **Run workflow**
3. Enter version (e.g., `1.2.0`)
4. Optionally enable **dry run** to test without releasing
5. Click **Run workflow**

## Release Artifacts

| Artifact | Location |
|----------|----------|
| Docker image | `ghcr.io/paolino/whisper-server:X.Y.Z` |
| Docker latest | `ghcr.io/paolino/whisper-server:latest` |
| Git tag | `vX.Y.Z` |
| GitHub Release | Auto-generated notes |
