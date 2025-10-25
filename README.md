# PacketClaude

An AX.25 packet radio gateway that allows amateur radio operators to interact with Claude AI via VHF/UHF radio using packet radio.

## Overview

PacketClaude creates a packet radio BBS-style node that ham radio operators can connect to using AX.25 packet radio. Once connected, users can have conversations with Claude AI, with context preserved throughout their session.

![Demo using Packet Commander](docs/demo.png)

## Features

- **AX.25 Packet Radio Interface**: Connect via Direwolf software TNC
- **Radio Control**: Integrates with Yaesu FTX-1 via Hamlib for PTT control
- **Multi-user Support**: Handle multiple concurrent connections
- **Session Management**: Per-callsign conversation context
- **Rate Limiting**: Configurable usage limits per callsign
- **Activity Logging**: Complete audit trail of all interactions
- **Graceful Error Handling**: Robust handling of network, API, and radio issues

## Requirements

- Python 3.11 or higher
- Direwolf software TNC (configured and running)
- Yaesu FTX-1 radio with Hamlib support
- Anthropic API key for Claude access
- Sound card interface or hardware TNC for radio connection

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd PacketClaude
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the example configuration:
```bash
cp .env.example .env
cp config/config.yaml.example config/config.yaml
```

4. Edit configuration files with your settings:
- Add your Anthropic API key to `.env`
- Update `config/config.yaml` with your callsign and radio settings

## Configuration

### Main Configuration (`config/config.yaml`)

```yaml
station:
  callsign: "N0CALL-10"  # Your station callsign with SSID
  description: "PacketClaude AI Gateway"

direwolf:
  host: "localhost"
  port: 8001  # Direwolf KISS TCP port

radio:
  enabled: true
  model: "FTX-1"
  device: "/dev/ttyUSB0"
  baud: 4800

claude:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 500
  temperature: 0.7

rate_limits:
  queries_per_hour: 10
  max_response_chars: 1024
```

### Environment Variables (`.env`)

```
ANTHROPIC_API_KEY=your_api_key_here
LOG_LEVEL=INFO
```

## Usage

1. Ensure Direwolf is running and configured for your radio
2. Start PacketClaude:
```bash
python -m src.packetclaude.main
```

3. Connect from another station using AX.25:
```
connect N0CALL-10
```

4. Once connected, simply type your questions and Claude will respond!

## How It Works

1. **Connection**: User connects to your station via AX.25 packet radio
2. **Authentication**: System validates callsign and checks rate limits
3. **Session Creation**: A new Claude conversation context is created for the callsign
4. **Interaction**: User messages are sent to Claude API, responses are transmitted back
5. **Context Preservation**: Conversation history is maintained for the session duration
6. **Logging**: All interactions are logged with callsign, timestamp, and content
7. **Disconnection**: When user disconnects, session context is cleared

## Project Structure

```
PacketClaude/
├── config/               # Configuration files
├── src/packetclaude/    # Main source code
│   ├── ax25/           # AX.25 and KISS protocol handling
│   ├── radio/          # Hamlib radio control
│   ├── claude/         # Claude API integration
│   ├── auth/           # Rate limiting
│   └── logging/        # Activity logging
├── logs/               # Log files
└── data/              # SQLite database
```

## License

[Your chosen license]

## Contributing

Contributions welcome! Please feel free to submit pull requests.

## Disclaimer

This software is for use by licensed amateur radio operators only. Users must comply with all applicable amateur radio regulations in their jurisdiction. The author(s) assume no liability for improper use.

## Support

For issues and questions, please open an issue on GitHub.

73!
