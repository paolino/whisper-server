{
  pkgs,
  version,
}:
let
  pythonEnv = pkgs.python3.withPackages (
    ps: with ps; [
      websockets
      numpy
      pydantic
      pydantic-settings
      pip
    ]
  );

  startScript = pkgs.writeShellScript "start-whisper-server" ''
    set -euo pipefail
    export PATH="${pkgs.ffmpeg}/bin:$PATH"
    export HOME=/tmp
    export PIP_TARGET=/tmp/pip-packages
    pip install --quiet faster-whisper
    if [ "''${WHISPER_LLAMA_ENABLED:-false}" = "true" ]; then
      pip install --quiet llama-cpp-python
    fi
    export PYTHONPATH="/app:$PIP_TARGET:''${PYTHONPATH:-}"
    exec python /app/server.py
  '';
in
pkgs.dockerTools.buildImage {
  name = "ghcr.io/paolino/whisper-server";
  tag = version;

  copyToRoot = pkgs.buildEnv {
    name = "whisper-server-root";
    paths = [
      pythonEnv
      pkgs.ffmpeg
      pkgs.cacert
      pkgs.stdenv.cc.cc.lib
    ];
    pathsToLink = [
      "/bin"
      "/lib"
    ];
  };

  extraCommands = ''
    mkdir -p app tmp
    cp -r ${../src}/* app/
  '';

  config = {
    Cmd = [ startScript ];
    WorkingDir = "/app";
    ExposedPorts = {
      "9002/tcp" = { };
    };
    Env = [
      "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
      "LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib"
      "WHISPER_MODEL=base"
      "WHISPER_HOST=0.0.0.0"
      "WHISPER_PORT=9002"
      "WHISPER_LLAMA_ENABLED=false"
    ];
    Labels = {
      "org.opencontainers.image.source" = "https://github.com/paolino/whisper-server";
      "org.opencontainers.image.description" = "Speech-to-text server using faster-whisper, compatible with Konele Android app";
      "org.opencontainers.image.licenses" = "MIT";
      "org.opencontainers.image.version" = version;
    };
  };
}
