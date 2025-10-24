# PacketClaude Running Modes

PacketClaude can run in three different modes depending on your needs.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run in telnet-only mode (no radio needed - great for testing!)
./packetclaude.py --telnet-only

# Connect
telnet localhost 8023
```

## Running Modes

### 1. Full Mode (Default)

Both packet radio (KISS/Direwolf) and telnet interfaces are enabled.

```bash
./packetclaude.py
```

**Requirements:**
- Direwolf must be running and configured
- Radio hardware (if radio control enabled)
- Config file: `config/config.yaml`

**Use Cases:**
- Production packet radio gateway
- Monitor both radio and telnet connections
- Full ham radio station integration

### 2. Telnet-Only Mode

**No radio or Direwolf required!** Perfect for development and testing.

```bash
./packetclaude.py --telnet-only
```

**Requirements:**
- Only Python and dependencies
- No Direwolf needed
- No radio hardware needed

**Use Cases:**
- Development and testing
- Demo/presentation mode
- Remote-only access (no radio)
- Learning Claude API integration

**Benefits:**
- Fast startup (no Direwolf connection)
- Easy to test locally
- No radio license required
- Great for development

### 3. KISS-Only Mode

Radio interface only, no telnet server.

```bash
./packetclaude.py --kiss-only
```

**Requirements:**
- Direwolf running
- Radio hardware configured

**Use Cases:**
- Production radio gateway
- Security (no network exposure)
- Dedicated radio-only station

## Command-Line Options

### Interface Modes

```bash
--telnet-only          # Disable KISS/Direwolf, enable telnet only
--kiss-only            # Disable telnet, enable KISS/Direwolf only
# (no flag)            # Enable both interfaces
```

### Configuration Overrides

```bash
-c, --config PATH      # Use custom config file
--telnet-port PORT     # Override telnet port (default: 8023)
--telnet-host HOST     # Override telnet host (default: localhost)
--direwolf-host HOST   # Override Direwolf host (default: localhost)
--direwolf-port PORT   # Override Direwolf port (default: 8001)
```

## Examples

### Development/Testing

```bash
# Start telnet-only on default port
./packetclaude.py --telnet-only

# Use custom telnet port
./packetclaude.py --telnet-only --telnet-port 8888

# Use custom config
./packetclaude.py --telnet-only -c /path/to/test-config.yaml
```

### Production Radio

```bash
# Standard radio gateway
./packetclaude.py

# Radio only (no telnet)
./packetclaude.py --kiss-only

# Custom Direwolf port
./packetclaude.py --direwolf-port 8002
```

### Remote Access

```bash
# Telnet accessible from network
./packetclaude.py --telnet-only --telnet-host 0.0.0.0

# Custom port for remote access
./packetclaude.py --telnet-only --telnet-host 0.0.0.0 --telnet-port 9000
```

## Alternative Launch Methods

### Using Python Module

```bash
python -m src.packetclaude.main --telnet-only
```

### Using Launcher Script

```bash
./packetclaude.py --help
```

### Old Shell Script (deprecated)

```bash
./scripts/run.sh
# Note: This doesn't support --telnet-only flag
```

## Environment Variables

PacketClaude reads configuration from:

1. **Config file**: `config/config.yaml` (or via `-c`)
2. **Environment**: `.env` file or system environment
   - `ANTHROPIC_API_KEY` - Required for Claude API
   - `CONFIG_PATH` - Override default config path

## Startup Validation

PacketClaude validates environment before starting:

✅ **Checks:**
- Config file exists
- API key available (warns if missing)
- Port availability (for telnet mode)
- Direwolf connection (for KISS mode)

❌ **Fails if:**
- Config file not found
- Direwolf unreachable (in KISS modes)
- Telnet port in use (in telnet modes)

## Logs

All modes log to `logs/packetclaude_YYYYMMDD.log`

View logs:
```bash
tail -f logs/packetclaude_*.log
```

## Troubleshooting

### Telnet-Only Mode

**Port already in use:**
```bash
./packetclaude.py --telnet-only --telnet-port 8024
```

**Can't connect:**
```bash
# Check if running
ps aux | grep packetclaude

# Check port
lsof -i :8023

# Test connection
telnet localhost 8023
```

### KISS Mode

**Can't connect to Direwolf:**
```bash
# Check Direwolf is running
ps aux | grep direwolf

# Check Direwolf KISS port
grep KISSPORT /etc/direwolf.conf

# Test Direwolf connection
telnet localhost 8001
```

**Use telnet-only instead:**
```bash
./packetclaude.py --telnet-only
```

## Performance

### Startup Times

- **Telnet-only**: ~1 second (fast!)
- **KISS mode**: ~2-5 seconds (Direwolf connection)
- **Full mode**: ~2-5 seconds

### Resource Usage

- **CPU**: Low (<5% idle, <20% active)
- **Memory**: ~50-100 MB
- **Network**: Minimal (only API calls)

## Security Considerations

### Telnet-Only Mode

- **Default**: Binds to `localhost` (local access only)
- **Network**: Use `--telnet-host 0.0.0.0` for remote access
- **Warning**: Telnet is unencrypted!
- **Firewall**: Ensure port is protected if exposed

### Recommendations

1. Use `localhost` for local testing only
2. Use VPN/SSH tunnel for remote access
3. Configure firewall rules for network exposure
4. Monitor `logs/` for suspicious activity

## Migration from Shell Script

**Old way:**
```bash
./scripts/run.sh
```

**New way (equivalent):**
```bash
./packetclaude.py
```

**New way (telnet-only):**
```bash
./packetclaude.py --telnet-only
```

The shell script still works but doesn't support the new flags. Use the Python launcher for full functionality.
