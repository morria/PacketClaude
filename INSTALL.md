# PacketClaude Installation Guide

Complete installation instructions for PacketClaude.

## System Requirements

- **Operating System**: Linux, macOS, or Windows (Linux recommended for production)
- **Python**: 3.11 or higher
- **RAM**: 512MB minimum, 1GB recommended
- **Storage**: 500MB for application and logs
- **Radio**: Yaesu FTX-1 or compatible transceiver
- **TNC**: Direwolf software TNC (recommended) or hardware TNC with KISS support
- **Internet**: Required for Claude API access

## Step 1: Install System Dependencies

### Linux (Debian/Ubuntu)

```bash
# Update package list
sudo apt-get update

# Install Python and development tools
sudo apt-get install python3.11 python3-pip python3-venv git

# Install Direwolf
sudo apt-get install direwolf

# Install Hamlib (optional, for radio control)
sudo apt-get install libhamlib-dev python3-libhamlib

# Install audio dependencies for Direwolf
sudo apt-get install libasound2-dev
```

### Linux (Fedora/RHEL)

```bash
# Install Python
sudo dnf install python3.11 python3-pip git

# Install Direwolf (may need to build from source)
sudo dnf install cmake gcc-c++ alsa-lib-devel

# Install Hamlib
sudo dnf install hamlib hamlib-devel
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11
brew install direwolf
brew install hamlib
```

### Windows

1. Install Python 3.11+ from https://www.python.org/downloads/
2. Install Direwolf for Windows from https://github.com/wb2osz/direwolf/releases
3. Hamlib support on Windows is limited - consider using Linux in a VM

## Step 2: Install PacketClaude

### Clone the Repository

```bash
cd ~
git clone https://github.com/yourusername/PacketClaude.git
cd PacketClaude
```

Or if you received it as a zip file:
```bash
cd ~
unzip PacketClaude.zip
cd PacketClaude
```

### Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Configure Direwolf

### Create Direwolf Configuration

Create `~/direwolf.conf`:

```bash
# Audio device - adjust for your system
# Use 'aplay -l' to list devices on Linux
ADEVICE plughw:1,0

# Channel configuration
ACHANNELS 1
CHANNEL 0

# Your callsign
MYCALL N0CALL-1

# Modem settings for 1200 baud VHF
MODEM 1200

# PTT control
# Option 1: Via Hamlib
PTT RIG 2 /dev/ttyUSB0

# Option 2: Via GPIO (Raspberry Pi)
# PTT GPIO 17

# Option 3: Via CAT control serial
# PTT /dev/ttyUSB0 RTS

# Enable KISS TCP server
KISSPORT 8001

# Optional: Enable AGW protocol
# AGWPORT 8000

# Logging
LOGDIR /home/pi/direwolf-logs
```

### Test Direwolf

```bash
# Start Direwolf
direwolf -c ~/direwolf.conf

# You should see:
# - Audio device opened successfully
# - Ready to accept KISS TCP client on port 8001
# - Listening for packets...
```

Press Ctrl+C to stop after verifying it works.

## Step 4: Configure PacketClaude

### Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (you won't see it again!)

### Setup Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env
nano .env
```

Add your API key:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
LOG_LEVEL=INFO
```

### Setup Configuration

```bash
# Copy template
cp config/config.yaml.example config/config.yaml

# Edit configuration
nano config/config.yaml
```

Key settings to change:

```yaml
station:
  callsign: "YOUR_CALL-10"  # CHANGE THIS to your callsign!

direwolf:
  host: "localhost"
  port: 8001

radio:
  enabled: true
  model: "FTX-1"
  device: "/dev/ttyUSB0"  # Check with: ls /dev/ttyUSB*
  baud: 4800

claude:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 500  # Adjust for your needs
  temperature: 0.7

rate_limits:
  queries_per_hour: 10
  queries_per_day: 50
```

## Step 5: Verify Installation

```bash
# Run verification script
python scripts/verify_install.py

# This will check:
# - Python version
# - Dependencies
# - Configuration files
# - Directory structure
# - Module imports
```

Fix any issues reported before proceeding.

## Step 6: Test Components

### Test KISS Connection

```bash
# Start Direwolf in another terminal
direwolf -c ~/direwolf.conf

# In your PacketClaude terminal:
python scripts/test_kiss.py
```

This tests that PacketClaude can connect to Direwolf.

### Test Radio Control (Optional)

If using Hamlib:

```bash
# Test radio communication
rigctl -m 1044 -r /dev/ttyUSB0 -s 4800

# Try commands:
# f        - Get frequency
# m        - Get mode
# t        - Get PTT status
# \q       - Quit
```

## Step 7: Run PacketClaude

### Manual Start

```bash
# Make sure Direwolf is running in another terminal
direwolf -c ~/direwolf.conf

# Start PacketClaude
./scripts/run.sh
```

You should see:
```
============================================================
PacketClaude - AX.25 Packet Radio Gateway for Claude AI
============================================================
INFO - Connecting to Direwolf at localhost:8001
INFO - Connected to KISS TNC at localhost:8001
INFO - PacketClaude ready - listening as YOUR_CALL-10
INFO - Press Ctrl+C to stop
```

### As a System Service (Linux)

For production use, run as a systemd service:

```bash
# Edit service file
sudo nano /etc/systemd/system/packetclaude.service

# Copy contents from scripts/packetclaude.service
# Update paths and user as needed

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start at boot
sudo systemctl enable packetclaude

# Start service
sudo systemctl start packetclaude

# Check status
sudo systemctl status packetclaude

# View logs
sudo journalctl -u packetclaude -f
```

## Step 8: Test from Another Station

### Using a Terminal Program

Connect to your station:
```
connect YOUR_CALL-10
```

Try commands:
```
help
What is ham radio?
status
73
```

### Using Another Computer

If you have another computer with packet radio:

1. Configure it to connect to the same frequency
2. Connect to YOUR_CALL-10
3. Send test messages

## Troubleshooting

### "Failed to connect to Direwolf"

- Check Direwolf is running: `ps aux | grep direwolf`
- Verify KISSPORT setting in direwolf.conf
- Check firewall: `sudo ufw allow 8001` (if using UFW)

### "Radio control failed"

- Check device exists: `ls -l /dev/ttyUSB0`
- Check permissions: `sudo chmod 666 /dev/ttyUSB0`
- Add user to dialout group: `sudo usermod -a -G dialout $USER`
- Verify Hamlib model number for your radio
- Or disable radio control: set `radio.enabled: false`

### "API key invalid"

- Verify API key in .env is correct
- Check for extra spaces or newlines
- Verify key has credits at console.anthropic.com
- Test key with: `curl https://api.anthropic.com/v1/messages -H "anthropic-version: 2023-06-01" -H "x-api-key: YOUR_KEY" -H "content-type: application/json" -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'`

### "No audio from Direwolf"

- Check audio device: `aplay -l` (Linux)
- Test audio: `speaker-test`
- Verify sound card connections
- Check volume levels: `alsamixer`

### Permission Errors

```bash
# Give access to serial ports
sudo usermod -a -G dialout $USER

# Give access to audio
sudo usermod -a -G audio $USER

# Log out and back in for changes to take effect
```

## Upgrading

```bash
# Stop PacketClaude
sudo systemctl stop packetclaude  # If running as service
# Or press Ctrl+C if running manually

# Pull latest changes
cd ~/PacketClaude
git pull

# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart
sudo systemctl start packetclaude  # If running as service
# Or ./scripts/run.sh
```

## Uninstalling

```bash
# Stop service
sudo systemctl stop packetclaude
sudo systemctl disable packetclaude

# Remove service file
sudo rm /etc/systemd/system/packetclaude.service
sudo systemctl daemon-reload

# Remove installation
cd ~
rm -rf PacketClaude

# Optional: Remove Direwolf
sudo apt-get remove direwolf  # Linux
brew uninstall direwolf        # macOS
```

## Next Steps

- Read QUICKSTART.md for usage instructions
- Customize config/config.yaml for your setup
- Check logs/ directory for activity
- Monitor data/sessions.db for statistics

## Getting Help

- Check README.md for documentation
- Review logs in logs/ directory
- Open issue on GitHub
- Join the discussion (if applicable)

73!
