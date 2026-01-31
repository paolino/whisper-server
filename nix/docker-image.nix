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
    pip install --quiet --user faster-whisper
    export PYTHONPATH="/app:$HOME/.local/lib/python3.12/site-packages:$PYTHONPATH"
    python /app/server.py
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
      "WHISPER_MODEL=base"
      "WHISPER_HOST=0.0.0.0"
      "WHISPER_PORT=9002"
    ];
  };
}
