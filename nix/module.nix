{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.whisper-server;

  pythonEnv = pkgs.python3.withPackages (
    ps: with ps; [
      websockets
      aiohttp
      numpy
      pydantic
      pydantic-settings
      pip
    ]
  );

  startScript = pkgs.writeShellScript "start-whisper-server" ''
    set -euo pipefail
    export HOME=/var/lib/whisper-server
    export PATH="${pkgs.ffmpeg}/bin:${pythonEnv}/bin:$PATH"

    # Determine host address
    if [[ "$WHISPER_TAILSCALE" == "true" ]]; then
      WHISPER_HOST="$(${pkgs.tailscale}/bin/tailscale ip -4)"
      export WHISPER_HOST
    fi

    # Install faster-whisper if not present
    if ! python -c "import faster_whisper" 2>/dev/null; then
      pip install --quiet --user faster-whisper
    fi
    export PYTHONPATH="$WHISPER_SRC:$HOME/.local/lib/python3.12/site-packages:$PYTHONPATH"

    exec python "$WHISPER_SRC/server.py"
  '';
in
{
  options.services.whisper-server = {
    enable = lib.mkEnableOption "Whisper speech-to-text server";

    package = lib.mkOption {
      type = lib.types.path;
      description = "Path to the whisper-server source directory.";
    };

    host = lib.mkOption {
      type = lib.types.str;
      default = "127.0.0.1";
      description = ''
        Address to listen on. Set to "0.0.0.0" for all interfaces.
        Ignored when tailscale.enable is true.
      '';
    };

    port = lib.mkOption {
      type = lib.types.port;
      default = 9002;
      description = "WebSocket port to listen on.";
    };

    httpPort = lib.mkOption {
      type = lib.types.port;
      default = 9003;
      description = "HTTP port for /transcribe endpoint.";
    };

    model = lib.mkOption {
      type = lib.types.enum [
        "tiny"
        "base"
        "small"
        "medium"
        "large-v3"
      ];
      default = "base";
      description = "Whisper model to use.";
    };

    device = lib.mkOption {
      type = lib.types.str;
      default = "auto";
      description = "Compute device (auto, cpu, cuda).";
    };

    computeType = lib.mkOption {
      type = lib.types.str;
      default = "auto";
      description = "Compute type (auto, int8, float16, float32).";
    };

    language = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "Language code for transcription (null for auto-detect).";
    };

    tailscale = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = false;
        description = "Listen only on Tailscale interface.";
      };

      interface = lib.mkOption {
        type = lib.types.str;
        default = "tailscale0";
        description = "Tailscale network interface name.";
      };
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.whisper-server = {
      description = "Whisper Speech-to-Text Server";
      after = [
        "network.target"
      ] ++ lib.optional cfg.tailscale.enable "tailscaled.service";
      wantedBy = [ "multi-user.target" ];
      wants = lib.optional cfg.tailscale.enable "tailscaled.service";

      environment = {
        WHISPER_HOST = cfg.host;
        WHISPER_PORT = toString cfg.port;
        WHISPER_HTTP_PORT = toString cfg.httpPort;
        WHISPER_MODEL = cfg.model;
        WHISPER_DEVICE = cfg.device;
        WHISPER_COMPUTE_TYPE = cfg.computeType;
        WHISPER_SRC = cfg.package;
        WHISPER_TAILSCALE = lib.boolToString cfg.tailscale.enable;
      } // lib.optionalAttrs (cfg.language != null) { WHISPER_LANGUAGE = cfg.language; };

      serviceConfig = {
        Type = "simple";
        ExecStart = startScript;
        Restart = "on-failure";
        RestartSec = "5s";

        DynamicUser = true;
        StateDirectory = "whisper-server";

        NoNewPrivileges = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        PrivateTmp = true;
        PrivateDevices = true;
        ProtectKernelTunables = true;
        ProtectKernelModules = true;
        ProtectControlGroups = true;
        RestrictNamespaces = true;
        RestrictRealtime = true;
        RestrictSUIDSGID = true;
      };
    };

    networking.firewall = lib.mkIf cfg.tailscale.enable {
      interfaces.${cfg.tailscale.interface}.allowedTCPPorts = [
        cfg.port
        cfg.httpPort
      ];
    };
  };
}
