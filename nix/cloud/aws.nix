{
  config,
  lib,
  pkgs,
  modulesPath,
  ...
}:
{
  imports = [
    (modulesPath + "/virtualisation/amazon-image.nix")
    ./common.nix
  ];

  # Hostname (mkForce required to override amazon-image.nix default)
  networking.hostName = lib.mkForce "whisper-aws";

  # AWS metadata service access (for instance identity)
  networking.firewall.allowedTCPPorts = lib.mkAfter [ ];

  # EC2 uses DHCP
  networking.useDHCP = true;

  # GPU support for g4dn/g5 instances (uncomment if using GPU)
  # boot.kernelModules = [ "nvidia" ];
  # hardware.nvidia = {
  #   modesetting.enable = true;
  #   powerManagement.enable = false;
  #   open = false;
  #   nvidiaSettings = true;
  # };
  # hardware.opengl.enable = true;
  # services.whisper-server.device = "cuda";

  # Ensure IMDSv2 works (AWS metadata service)
  systemd.services.whisper-server.serviceConfig = {
    # Allow access to metadata endpoint
    IPAddressAllow = [
      "169.254.169.254"
      "100.64.0.0/10"
    ]; # metadata + Tailscale
  };
}
