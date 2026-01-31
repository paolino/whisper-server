{
  config,
  lib,
  pkgs,
  whisperServerSrc,
  ...
}:
{
  imports = [ ];

  # Tailscale for secure private networking
  services.tailscale = {
    enable = true;
    useRoutingFeatures = "client";
  };

  # Whisper server with Tailscale-only access
  services.whisper-server = {
    enable = true;
    package = whisperServerSrc;
    model = lib.mkDefault "base";
    device = lib.mkDefault "cpu";
    tailscale = {
      enable = true;
      interface = "tailscale0";
    };
  };

  # Firewall: SSH only on public, whisper on Tailscale
  networking.firewall = {
    enable = true;
    allowedTCPPorts = [ 22 ];
    interfaces.tailscale0.allowedTCPPorts = [ 9002 ];
  };

  # SSH hardening: key-based auth only
  services.openssh = {
    enable = true;
    settings = {
      PasswordAuthentication = false;
      PermitRootLogin = "prohibit-password";
      KbdInteractiveAuthentication = false;
    };
  };

  # Auto-updates for security patches
  system.autoUpgrade = {
    enable = true;
    allowReboot = false;
    dates = "04:00";
    flake = "github:paolino/whisper-server";
  };

  # zram swap for memory pressure
  zramSwap = {
    enable = true;
    memoryPercent = 50;
  };

  # Basic system packages
  environment.systemPackages = with pkgs; [
    vim
    htop
    curl
    jq
    git
  ];

  # Use systemd-resolved for DNS
  services.resolved.enable = true;

  # Timezone
  time.timeZone = lib.mkDefault "UTC";

  # NixOS settings
  nix = {
    settings = {
      auto-optimise-store = true;
      experimental-features = [
        "nix-command"
        "flakes"
      ];
    };
    gc = {
      automatic = true;
      dates = "weekly";
      options = "--delete-older-than 30d";
    };
  };

  system.stateVersion = "24.11";
}
