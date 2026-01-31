# Cloud Deployment

Deploy whisper-server on Hetzner, AWS, or GCP with Tailscale-only access.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/paolino/whisper-server
cd whisper-server

# Build a configuration (choose one)
just build-cloud hetzner
just build-cloud aws
just build-cloud gcp

# Or build cloud images for AWS/GCP
just build-aws-ami
just build-gcp-image
```

## Available Configurations

| Configuration | Command | Use Case |
|--------------|---------|----------|
| `whisper-hetzner` | `just build-cloud hetzner` | Hetzner Cloud VPS |
| `whisper-aws` | `just build-cloud aws` | AWS EC2 instances |
| `whisper-gcp` | `just build-cloud gcp` | GCP Compute Engine |

## What's Included

All configurations provide:

- **Tailscale-only access** - Port 9002 not exposed to public internet
- **SSH hardening** - Key-based authentication only
- **Firewall** - Only SSH (22) open publicly
- **Auto-updates** - Daily security updates at 04:00 UTC
- **zram swap** - Memory efficiency for smaller instances

## Instance Sizing

Choose instance size based on the Whisper model:

| Model | RAM | Hetzner | AWS | GCP |
|-------|-----|---------|-----|-----|
| tiny | 2GB | CPX11 (~4€) | t3.small (~$15) | e2-small (~$12) |
| base | 4GB | CPX21 (~8€) | t3.medium (~$30) | e2-medium (~$24) |
| small | 8GB | CPX31 (~15€) | t3.large (~$60) | e2-standard-2 (~$48) |
| medium | 16GB | CPX41 (~30€) | t3.xlarge (~$120) | e2-standard-4 (~$96) |
| large-v3 | 32GB | CPX51 (~60€) | g4dn.xlarge (~$380) | n1+T4 (~$350) |

## Prerequisites

1. Tailscale account (free, see setup below)
2. Cloud provider account
3. SSH key pair
4. Nix with flakes enabled

---

## Tailscale Setup

Tailscale creates a private network (called a "tailnet") between your devices. Your whisper server will only be accessible from devices on your tailnet - not from the public internet.

### Why Tailscale?

- **Security**: Server not exposed to the internet
- **No port forwarding**: Works behind NAT/firewalls
- **Easy mobile access**: Android app connects automatically
- **Free tier**: Up to 100 devices

### Step 1: Create Account

1. Go to [tailscale.com](https://tailscale.com/)
2. Click "Get Started"
3. Sign up with Google, Microsoft, GitHub, or email

### Step 2: Install on Your Devices

Install Tailscale on every device that needs to access the whisper server:

**Android (for Konele):**

1. Install [Tailscale from Play Store](https://play.google.com/store/apps/details?id=com.tailscale.ipn)
2. Open app and sign in with same account
3. Toggle "Connected" on

**Linux/Mac/Windows:**

```bash
# macOS
brew install tailscale

# Ubuntu/Debian
curl -fsSL https://tailscale.com/install.sh | sh

# Then connect
sudo tailscale up
```

Or download from [tailscale.com/download](https://tailscale.com/download)

### Step 3: Generate Auth Key for Server

The cloud server needs an auth key to join your tailnet automatically:

1. Log in at [login.tailscale.com](https://login.tailscale.com/)
2. Click **Settings** (bottom of left sidebar)
3. Click **Keys** (under Personal Settings)
4. Click **Generate auth key**
5. Settings:
    - **Reusable**: Yes (for testing) or No (more secure)
    - **Expiration**: 90 days is fine
    - **Tags**: Optional, leave empty
6. Click **Generate key**
7. Copy the key (starts with `tskey-auth-`)

Save this key - you'll use it after deploying the server.

### Step 4: After Server Deployment

Once your server is running, SSH in and connect it to Tailscale:

```bash
ssh root@<server-public-ip>
sudo tailscale up --authkey=tskey-auth-XXXXX
```

Verify it's connected:

```bash
tailscale status
```

You should see your server listed along with your other devices.

### Step 5: Verify Connectivity

From any device on your tailnet:

```bash
# Using the Tailscale hostname
ping whisper-hetzner

# Or using the Tailscale IP (100.x.x.x)
tailscale status  # shows IPs
ping 100.x.x.x
```

### Finding Your Server

After connecting, your server is reachable by:

- **Hostname**: `whisper-hetzner`, `whisper-aws`, or `whisper-gcp`
- **Tailscale IP**: `100.x.x.x` (shown in `tailscale status`)
- **MagicDNS**: `whisper-hetzner.your-tailnet.ts.net`

For Konele, use: `ws://whisper-hetzner:9002/ws`

---

## Hetzner Cloud

Best price/performance for CPU workloads.

### Option 1: Deploy to Existing NixOS Server

If you already have NixOS running on Hetzner:

```bash
# From your local machine
just deploy-hetzner root@your-server-ip
```

### Option 2: Fresh Install with nixos-anywhere

```bash
# Install nixos-anywhere
nix profile install github:nix-community/nixos-anywhere

# Deploy (will wipe the server!)
nixos-anywhere --flake .#whisper-hetzner root@your-server-ip
```

### Option 3: Manual Installation

1. Boot Hetzner server into rescue mode (NixOS ISO)
2. Partition and mount disk at `/mnt`
3. Install:

```bash
nixos-install --flake github:paolino/whisper-server#whisper-hetzner
reboot
```

### After Installation

```bash
# SSH into server
ssh root@your-server-ip

# Connect to Tailscale
sudo tailscale up --authkey=tskey-auth-XXXXX

# Verify whisper-server is running
systemctl status whisper-server
```

---

## AWS EC2

### Step 1: Build the AMI

```bash
just build-aws-ami
# Output: result/nixos-amazon-image-*.raw
```

### Step 2: Upload to S3

```bash
# Create bucket if needed
aws s3 mb s3://my-nixos-images

# Upload image
aws s3 cp result/nixos-amazon-image-*.raw s3://my-nixos-images/whisper.raw
```

### Step 3: Import as AMI

```bash
# Create import task
aws ec2 import-image \
    --description "whisper-server NixOS" \
    --disk-containers "Format=RAW,UserBucket={S3Bucket=my-nixos-images,S3Key=whisper.raw}"

# Check import status (takes 10-30 minutes)
aws ec2 describe-import-image-tasks
```

### Step 4: Launch Instance

```bash
# Get the AMI ID from the completed import task
AMI_ID=$(aws ec2 describe-import-image-tasks \
    --query 'ImportImageTasks[0].ImageId' --output text)

# Create security group (SSH only)
aws ec2 create-security-group \
    --group-name whisper-sg \
    --description "Whisper server - SSH only"

aws ec2 authorize-security-group-ingress \
    --group-name whisper-sg \
    --protocol tcp --port 22 --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type t3.medium \
    --key-name your-key-name \
    --security-groups whisper-sg
```

### Step 5: Configure Tailscale

```bash
# Get instance IP
aws ec2 describe-instances --query 'Reservations[*].Instances[*].PublicIpAddress'

# SSH and configure
ssh root@<instance-ip>
sudo tailscale up --authkey=tskey-auth-XXXXX
```

---

## GCP Compute Engine

### Step 1: Build the Image

```bash
just build-gcp-image
# Output: result/nixos-google-compute-image-*.raw.tar.gz
```

### Step 2: Upload to Cloud Storage

```bash
# Create bucket if needed
gsutil mb gs://my-nixos-images

# Upload image
gsutil cp result/nixos-google-compute-image-*.raw.tar.gz \
    gs://my-nixos-images/whisper.tar.gz
```

### Step 3: Create Compute Image

```bash
gcloud compute images create whisper-server \
    --source-uri gs://my-nixos-images/whisper.tar.gz \
    --guest-os-features VIRTIO_SCSI_MULTIQUEUE,UEFI_COMPATIBLE
```

### Step 4: Launch Instance

```bash
# Create firewall rule (SSH only)
gcloud compute firewall-rules create whisper-ssh \
    --allow tcp:22 \
    --target-tags whisper

# Launch instance
gcloud compute instances create whisper-server \
    --image whisper-server \
    --machine-type e2-medium \
    --zone us-central1-a \
    --tags whisper
```

### Step 5: Configure Tailscale

```bash
# SSH into instance
gcloud compute ssh whisper-server --zone us-central1-a

# Configure Tailscale
sudo tailscale up --authkey=tskey-auth-XXXXX
```

---

## Using Your Deployed Server

Once deployed and connected to Tailscale (see [Tailscale Setup](#tailscale-setup) above):

### From Android (Konele)

1. Ensure Tailscale is installed and connected on your phone
2. Open Konele settings
3. Set server URL to: `ws://whisper-hetzner:9002/ws`
   (replace `whisper-hetzner` with your server's hostname)

### Test from Command Line

```bash
# From any device on your Tailnet
curl http://whisper-server:9002/

# Or use the Tailscale IP
curl http://100.x.x.x:9002/
```

### Check Server Status

```bash
ssh root@whisper-server
systemctl status whisper-server
journalctl -u whisper-server -f
```

---

## Customization

### Change Whisper Model

Create a custom configuration that imports the base:

```nix
# my-whisper.nix
{ ... }:
{
  imports = [ ./nix/cloud/hetzner.nix ];
  services.whisper-server.model = "small";
}
```

Or edit the provider file directly:

```nix
# In nix/cloud/common.nix
services.whisper-server.model = "small";  # was "base"
```

### Enable GPU (AWS/GCP only)

Edit `nix/cloud/aws.nix` or `nix/cloud/gcp.nix` and uncomment the NVIDIA section:

```nix
boot.kernelModules = [ "nvidia" ];
hardware.nvidia = {
  modesetting.enable = true;
  powerManagement.enable = false;
  open = false;
  nvidiaSettings = true;
};
hardware.opengl.enable = true;
services.whisper-server.device = "cuda";
```

Then rebuild and redeploy.

### Custom Hostname

```nix
networking.hostName = "my-whisper";
```

### Different Language

```nix
services.whisper-server.language = "de";  # German
```

---

## Troubleshooting

### Tailscale Not Connected

```bash
# Check status
tailscale status

# Re-authenticate
sudo tailscale up --authkey=tskey-auth-XXXXX

# Check if service is running
systemctl status tailscaled
```

### Whisper Server Not Starting

```bash
# Check service status
systemctl status whisper-server

# View logs
journalctl -u whisper-server -f

# Common issue: model still downloading
journalctl -u whisper-server | grep -i download
```

### Cannot Connect from Phone

1. Verify phone is on the same Tailnet: `tailscale status` on both devices
2. Check firewall: `sudo iptables -L -n | grep 9002`
3. Test locally on server: `curl http://localhost:9002/`

### Out of Memory

Upgrade to a larger instance or use a smaller model:

```nix
services.whisper-server.model = "tiny";  # Uses ~1GB RAM
```

---

## Justfile Recipes Reference

| Recipe | Description |
|--------|-------------|
| `just build-cloud <target>` | Build NixOS config (hetzner/aws/gcp) |
| `just deploy-hetzner <host>` | Deploy to Hetzner via nixos-rebuild |
| `just build-aws-ami` | Build AWS AMI disk image |
| `just build-gcp-image` | Build GCP Compute image |
