{
  description = "Self-hosted Whisper speech-to-text server for Konele";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachSystem
      [
        "x86_64-linux"
        "aarch64-darwin"
      ]
      (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          version = self.dirtyShortRev or self.shortRev or "dev";

          pythonEnv = pkgs.python3.withPackages (
            ps: with ps; [
              websockets
              numpy
              pydantic
              pydantic-settings
            ]
          );

          dockerImage = import ./nix/docker-image.nix {
            inherit pkgs version;
          };
        in
        {
          packages = {
            docker-image = dockerImage;
            default = pythonEnv;
          };

          inherit version;

          devShells.default = pkgs.mkShell {
            buildInputs = [
              pythonEnv
              pkgs.ffmpeg
              pkgs.just
              pkgs.black
              pkgs.ruff
              pkgs.mypy
              pkgs.python3Packages.pytest
            ];

            shellHook = ''
              if [ ! -d .venv ]; then
                echo "Creating virtual environment..."
                python -m venv .venv
              fi
              source .venv/bin/activate
              if ! python -c "import faster_whisper" 2>/dev/null; then
                echo "Installing faster-whisper..."
                pip install --quiet faster-whisper
              fi
              export PYTHONPATH="$PWD/src:$PYTHONPATH"
            '';
          };
        }
      );
}
