{
  config,
  lib,
  pkgs,
  modulesPath,
  ...
}:
{
  imports = [
    (modulesPath + "/virtualisation/google-compute-image.nix")
    ./common.nix
  ];

  # Hostname (mkForce required to override google-compute-image.nix default)
  networking.hostName = lib.mkForce "whisper-gcp";

  # GCP uses DHCP
  networking.useDHCP = true;

  # GPU support for T4/A100 instances (uncomment if using GPU)
  # boot.kernelModules = [ "nvidia" ];
  # hardware.nvidia = {
  #   modesetting.enable = true;
  #   powerManagement.enable = false;
  #   open = false;
  #   nvidiaSettings = true;
  # };
  # hardware.opengl.enable = true;
  # services.whisper-server.device = "cuda";

  # GCP metadata service access
  systemd.services.whisper-server.serviceConfig = {
    # Allow access to metadata endpoint
    IPAddressAllow = [
      "169.254.169.254"
      "100.64.0.0/10"
    ]; # metadata + Tailscale
  };

  # GCP guest agent is included in google-compute-image.nix
}
