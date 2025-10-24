# Quick Start Guide

Get PacketClaude running in under 5 minutes!

## Prerequisites

- Python 3.8+
- Anthropic API key

## Installation

```bash
# 1. Clone or download PacketClaude
cd PacketClaude

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp config/config.yaml.example config/config.yaml
cp .env.example .env

# 5. Add your API key to .env
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

## Run in Telnet-Only Mode (No Radio Required!)

Perfect for testing and development:

```bash
./packetclaude.py --telnet-only
```

Output:
```
PacketClaude ready - telnet on localhost:8023
Press Ctrl+C to stop
Running in telnet-only mode (no KISS processing)
```

## Connect and Test

In another terminal:

```bash
telnet localhost 8023
```

**Tip**: PacketClaude will detect your login name and use it as your callsign! Set it with:
```bash
USER=K0ASM telnet localhost 8023
```

Try these commands:
```
help
what is amateur radio?
show me pota spots on 20m
who else is connected?
show me my session info
status
quit
```

## That's It!

You now have PacketClaude running with:
- ✅ Claude AI integration
- ✅ Web search capability
- ✅ POTA spots tool
- ✅ BBS session management (ask Claude for help, status, etc.)
- ✅ Automatic callsign detection from telnet login
- ✅ No radio hardware needed

## Next Steps

### For Ham Radio Use

See [docs/RUNNING_MODES.md](docs/RUNNING_MODES.md) for:
- Setting up with Direwolf
- Configuring radio control
- Running both radio and telnet interfaces

### Configuration

Edit `config/config.yaml`:
- Adjust rate limits
- Enable/disable tools (search, POTA)
- Configure telnet/KISS ports
- Set Claude API parameters

### Tools

PacketClaude includes:
- **Web Search**: Claude can search the internet
- **POTA Spots**: Live Parks on the Air activations
- More tools coming soon!

## Troubleshooting

**Port already in use?**
```bash
./packetclaude.py --telnet-only --telnet-port 8024
```

**Missing config?**
```bash
cp config/config.yaml.example config/config.yaml
```

**API key not found?**
```bash
export ANTHROPIC_API_KEY=your-key-here
```

## Documentation

- [Running Modes](docs/RUNNING_MODES.md) - Full, telnet-only, KISS-only
- [Telnet Login](docs/TELNET_LOGIN.md) - Automatic callsign detection
- [BBS Session Tool](docs/BBS_SESSION_TOOL.md) - Session management via Claude
- [POTA Tool](docs/POTA_TOOL.md) - Parks on the Air integration
- [Search Feature](docs/SEARCH_FEATURE.md) - Web search capability
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

## Getting Help

- Check logs: `tail -f logs/packetclaude_*.log`
- Run tests: `python scripts/test_pota.py`
- See `docs/TROUBLESHOOTING.md`

Happy hacking! 73 de PacketClaude 🎙️
