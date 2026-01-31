# Android Setup

This guide covers configuring Konele on your Android device to use your self-hosted Whisper server.

## Prerequisites

- Whisper Server running and accessible via Tailscale
- Android device on the same Tailscale network
- Your server's Tailscale IP (e.g., `100.64.1.42`)

## Install Konele

Konele (K6nele) is an open-source speech recognition app for Android.

1. Download the latest APK from [GitHub releases](https://github.com/Kaljurand/K6nele/releases)
2. Enable "Install from unknown sources" in Android settings if prompted
3. Install the APK

## Install Tailscale on Android

1. Install [Tailscale](https://play.google.com/store/apps/details?id=com.tailscale.ipn) from Play Store
2. Sign in with your Tailscale account
3. Ensure the connection is active

## Configure Konele

### Step 1: Open Konele Settings

1. Open Konele app
2. Tap the menu (three dots) → **Settings**
3. Go to **Recognition services**

### Step 2: Add Custom Server

1. Tap **Add server**
2. Configure as follows:

| Setting | Value |
|---------|-------|
| **Name** | Whisper (or any name) |
| **URL** | `ws://YOUR_TAILSCALE_IP:9002` |

Replace `YOUR_TAILSCALE_IP` with your server's Tailscale IP.

### Step 3: Set Audio Format

This is critical - Konele must send audio in the format the server expects:

1. In the server settings, find **Content-Type**
2. Set it to:

```
audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1
```

!!! warning "Audio Format"
    Using the wrong audio format will result in garbled transcriptions or errors.

### Step 4: Set as Default

1. Go back to **Recognition services**
2. Select your Whisper server as the default

## Enable as Input Method

To use Konele as a keyboard for voice input:

### Step 1: Enable in Android Settings

1. Go to Android **Settings** → **System** → **Languages & input**
2. Tap **On-screen keyboard** or **Virtual keyboard**
3. Tap **Manage keyboards**
4. Enable **Konele**

### Step 2: Switch Keyboards

When typing in any app:

1. Tap the keyboard icon in the navigation bar (or notification)
2. Select **Konele**
3. Tap the microphone button to start speaking

## Usage Tips

### Voice Input

1. Tap the microphone button
2. Speak clearly
3. Pause when done - the server will transcribe automatically
4. Text appears in the input field

### Quick Switch

Many Android keyboards show a microphone icon. Tapping it often launches Konele directly if configured as the default voice input.

### Language Selection

Konele can send a language hint to the server. Configure this in:

**Settings** → **Recognition services** → **Your server** → **Language**

The server will use this for better accuracy if configured.

## Troubleshooting

### Connection Failed

- Verify Tailscale is connected on both devices
- Check server is running: `curl -v ws://YOUR_IP:9002`
- Ensure port 9002 is open on the server's Tailscale interface

### No Transcription / Empty Results

- Check the audio format is set correctly
- Ensure you're speaking after tapping the microphone
- Check server logs for errors

### Garbled Transcription

- Audio format mismatch - verify Content-Type setting
- Try a larger Whisper model (medium, large)

### Slow Transcription

- Consider using a GPU on your server
- Use a smaller model (tiny, base)
- Reduce network latency (server geographically closer)

## Next Steps

- [Configuration](configuration.md) - Customize server options
- [Architecture](architecture.md) - Understand how it works
