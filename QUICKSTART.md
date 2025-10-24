# PacketClaude Quick Start Guide

This guide will help you get PacketClaude up and running quickly.

## Prerequisites

1. **Python 3.11+** installed
2. **Direwolf** software TNC installed and configured
3. **Yaesu FTX-1** radio (or compatible) with sound card interface
4. **Anthropic API Key** (get from https://console.anthropic.com/)
5. **Amateur Radio License** (required to operate)

## Installation Steps

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Optional: Install Hamlib for radio control
# On macOS:
brew install hamlib

# On Linux:
sudo apt-get install libhamlib-dev python3-libhamlib
```

### 2. Configure Direwolf

Create or edit your Direwolf configuration file (e.g., `direwolf.conf`):

```
ADEVICE plughw:1,0
ACHANNELS 1
CHANNEL 0
MYCALL N0CALL-1
MODEM 1200
PTT RIG 2 /dev/ttyUSB0

# Enable KISS TCP server
KISSPORT 8001
```

Start Direwolf:
```bash
direwolf -c direwolf.conf
```

### 3. Configure PacketClaude

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Anthropic API key:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

3. Edit `config/config.yaml`:
```yaml
station:
  callsign: "YOUR_CALL-10"  # Change to your callsign
  description: "PacketClaude AI Gateway"

direwolf:
  host: "localhost"
  port: 8001

radio:
  enabled: true
  model: "FTX-1"
  device: "/dev/ttyUSB0"  # Adjust for your setup
  baud: 4800

claude:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 500
  temperature: 0.7
```

### 4. Test Connection to Direwolf

Before running the full application, test your Direwolf connection:

```bash
python scripts/test_kiss.py
```

This will verify that PacketClaude can communicate with Direwolf.

### 5. Run PacketClaude

```bash
# Using the helper script
./scripts/run.sh

# Or directly
python -m src.packetclaude.main
```

## Testing

### From Another Station

Connect to your station using packet radio:

```
connect YOUR_CALL-10
```

Once connected, you can:
- Ask questions: Just type and send
- Get help: `help` or `?`
- Check status: `status`
- Clear history: `clear`
- Disconnect: `quit`, `bye`, or `73`

### Example Session

```
*** CONNECTED to YOUR_CALL-10

Welcome to PacketClaude!
You are now connected to Claude AI via packet radio.
Simply type your questions and press Enter.
Type 'help' for commands, 'quit' or 'bye' to disconnect.

> What is the speed of light?

...

The speed of light in vacuum is approximately 299,792,458 meters
per second (or about 186,282 miles per second). This is commonly
represented as 'c' in physics equations. This is the maximum speed
at which all conventional matter and information can travel.

> 73

73! Goodbye.

*** DISCONNECTED
```

## Troubleshooting

### Can't Connect to Direwolf
- Verify Direwolf is running: `ps aux | grep direwolf`
- Check KISSPORT is 8001 in direwolf.conf
- Verify no firewall blocking localhost:8001

### Radio Control Not Working
- Check Hamlib installation: `rigctl --version`
- Verify device path (e.g., /dev/ttyUSB0)
- Check permissions: `sudo chmod 666 /dev/ttyUSB0`
- Or disable radio control: set `radio.enabled: false` in config

### API Errors
- Verify API key is correct in .env
- Check internet connectivity
- Verify API key has credits at console.anthropic.com

### Rate Limits
- Default: 10 queries/hour, 50 queries/day per callsign
- Adjust in config/config.yaml under `rate_limits`
- Or disable: set `rate_limits.enabled: false`

## Directory Structure

```
PacketClaude/
├── config/
│   └── config.yaml          # Main configuration
├── logs/                    # Activity logs
├── data/
│   └── sessions.db         # SQLite database
├── src/packetclaude/       # Source code
└── scripts/                # Helper scripts
```

## Logs and Monitoring

- **Activity Logs**: `logs/packetclaude_YYYYMMDD.log`
- **Database**: `data/sessions.db` (SQLite - use any SQLite browser)
- **Console Output**: Real-time activity shown in terminal

## Next Steps

1. **Customize System Prompt**: Edit `claude.system_prompt` in config.yaml
2. **Adjust Rate Limits**: Modify `rate_limits` section in config.yaml
3. **Monitor Activity**: Check logs/ directory and database
4. **Optimize for Your Radio**: Adjust max_response_chars for your channel

## Safety Notes

- Always identify your station per FCC regulations
- Monitor your frequency before transmitting
- Respect band plans and frequency coordination
- Keep responses concise to minimize airtime
- Use appropriate power levels

## Support

For issues, questions, or contributions:
- GitHub Issues: [your-repo-url]
- Documentation: README.md

73 and happy packet radio!
