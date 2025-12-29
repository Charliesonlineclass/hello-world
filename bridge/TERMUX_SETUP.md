# SCORPION Bridge - Termux Setup Guide

Connect your Android phone to your Linux AI babies!

## Prerequisites

- Android phone
- Linux server with Ollama running
- Both devices on same network (or SSH tunnel)

## Step 1: Install Termux

1. **Download Termux** from F-Droid (NOT Play Store - outdated)
   - Go to: https://f-droid.org/packages/com.termux/
   - Or search "Termux" in F-Droid app

2. **Open Termux** and update packages:
   ```bash
   pkg update && pkg upgrade
   ```

## Step 2: Install Python

```bash
# Install Python
pkg install python

# Install pip packages
pip install requests
```

## Step 3: Get the Client

### Option A: Clone from GitHub
```bash
pkg install git
git clone https://github.com/YourUsername/hello-world.git
cd hello-world/bridge
```

### Option B: Direct Download
```bash
curl -O https://raw.githubusercontent.com/YourUsername/hello-world/main/bridge/termux_client.py
```

### Option C: Copy from Storage
```bash
# Grant storage permission
termux-setup-storage

# Copy from Downloads
cp ~/storage/downloads/termux_client.py .
```

## Step 4: Configure Server Connection

Find your Linux server's IP address:
```bash
# On Linux server
ip addr | grep "inet "
# Look for something like 192.168.1.100
```

Set environment variables in Termux:
```bash
# Add to ~/.bashrc for persistence
echo 'export BRIDGE_HOST="192.168.1.100"' >> ~/.bashrc
echo 'export BRIDGE_PORT="9876"' >> ~/.bashrc
echo 'export BRIDGE_API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc
```

Or set them temporarily:
```bash
export BRIDGE_HOST="192.168.1.100"
```

## Step 5: Start the Server (Linux)

On your Linux server:
```bash
cd ~/SCORPION_BRAIN
python3 -m bridge.phone_server
# Or
python3 bridge/phone_server.py
```

The server will start on port 9876.

## Step 6: Test Connection

In Termux:
```bash
# Check status
python termux_client.py status

# Ask MARCUS
python termux_client.py ask marcus "Hello, are you there?"

# Quick ask (uses HERMES)
python termux_client.py quick "What's 2+2?"

# Interactive mode
python termux_client.py interactive
```

## Using SSH Tunnel (Remote Access)

If your Linux server is not on the same network:

### On Linux Server
```bash
# Make sure SSH is running
sudo systemctl start sshd
```

### On Termux
```bash
# Install OpenSSH
pkg install openssh

# Create tunnel
ssh -L 9876:localhost:9876 user@your-server-ip

# Now use localhost as BRIDGE_HOST
export BRIDGE_HOST="localhost"
```

### Persistent Tunnel with autossh
```bash
pkg install autossh
autossh -M 0 -f -N -L 9876:localhost:9876 user@your-server-ip
```

## Quick Reference

```bash
# Ask a specific baby
python termux_client.py ask marcus "Your question"
python termux_client.py ask athena "Help me code this"
python termux_client.py ask apollo "Write a poem"

# Quick ask (fastest response)
python termux_client.py quick "Brief question"

# Search knowledge base
python termux_client.py search "meeting notes about project X"

# Check server status
python termux_client.py status

# List available babies
python termux_client.py babies

# Interactive chat
python termux_client.py interactive
```

## Available Babies

| Baby | Model | Best For |
|------|-------|----------|
| MARCUS | mistral | General questions, balanced |
| HERMES | phi | Fast answers, simple queries |
| ATHENA | codellama | Programming, code review |
| APOLLO | llama2 | Creative writing, content |

## Troubleshooting

### "Cannot connect to server"
1. Check server is running: `curl http://SERVER_IP:9876/status`
2. Check firewall: `sudo ufw allow 9876`
3. Verify IP address is correct

### "Connection refused"
1. Ensure Ollama is running on server
2. Check BRIDGE_HOST is set correctly
3. Verify server is listening: `netstat -tlnp | grep 9876`

### "Invalid API key"
1. Set BRIDGE_API_KEY to match server
2. Or use default key (only for local network)

### Slow responses
1. Use HERMES for faster responses: `python termux_client.py quick "..."`
2. Reduce max_tokens: `--max-tokens 100`
3. Check server has GPU acceleration

## Tips

1. **Create aliases** for quick access:
   ```bash
   echo 'alias ask="python ~/termux_client.py ask marcus"' >> ~/.bashrc
   echo 'alias qask="python ~/termux_client.py quick"' >> ~/.bashrc
   source ~/.bashrc

   # Now use:
   ask "What is the weather like?"
   qask "Quick question"
   ```

2. **Use Termux:Widget** for home screen shortcuts

3. **Use Termux:API** for voice input:
   ```bash
   pkg install termux-api
   python termux_client.py ask marcus "$(termux-speech-to-text)"
   ```

---

*SCORPION Bridge - Your AI, Everywhere* 🦂
