{
  config,
  lib,
  pkgs,
  modulesPath,
  ...
}:
{
  imports = [
    (modulesPath + "/profiles/qemu-guest.nix")
    ./common.nix
  ];

  # GRUB bootloader for Hetzner VPS
  boot.loader.grub = {
    enable = true;
    device = "/dev/sda";
  };

  # Root filesystem (adjust as needed for your disk layout)
  fileSystems."/" = {
    device = "/dev/sda1";
    fsType = "ext4";
  };

  # Cloud-init for initial setup
  services.cloud-init = {
    enable = true;
    network.enable = true;
  };

  # DHCP networking (Hetzner provides this)
  networking = {
    useDHCP = true;
    useNetworkd = true;
    hostName = lib.mkDefault "whisper-hetzner";
  };

  # Hetzner uses virtio
  boot.initrd.availableKernelModules = [
    "virtio_pci"
    "virtio_scsi"
    "ahci"
    "sd_mod"
  ];
}
