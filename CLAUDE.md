# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

### Start PacketClaude
```bash
# Standard mode (both KISS and telnet)
python -m src.packetclaude.main

# Telnet-only mode (no radio/Direwolf required for testing)
python -m src.packetclaude.main --telnet-only

# KISS-only mode (no telnet)
python -m src.packetclaude.main --kiss-only

# With custom config
python -m src.packetclaude.main -c /path/to/config.yaml

# Alternative launcher script
python packetclaude.py
```

### Testing & Development Scripts
```bash
# Verify installation
python scripts/verify_install.py

# Test KISS connection to Direwolf
python scripts/test_kiss.py

# Test telnet connection
python scripts/test_telnet.py

# Test specific tools
python scripts/test_pota.py
python scripts/test_qrz_api.py
python scripts/test_search.py
python scripts/test_bbs_tool.py

# Upload README.txt to file system for users
python scripts/upload_readme.py
```

## Debugging with Direwolf

**IMPORTANT**: Direwolf outputs logs to `logs/direwolf.log`. Check it to see what Direwolf most recently saw from the radio or KISS connections.

## Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Optional: Install Hamlib for radio control
# On macOS:
brew install hamlib

# On Linux:
sudo apt-get install libhamlib-dev python3-libhamlib
```

## Configuration

### Required Files
- `.env` - Contains `ANTHROPIC_API_KEY` and `LOG_LEVEL`
- `config/config.yaml` - Main configuration (copy from `config/config.yaml.example`)
- `config/direwolf.conf` - Direwolf TNC configuration (copy from `config/direwolf.conf.example`)

### Key Configuration Sections
- `station.callsign` - Your amateur radio callsign with SSID (e.g., "N0CALL-10")
- `direwolf.host` and `direwolf.port` - KISS TCP connection (default: localhost:8001)
- `telnet.port` - Telnet server port for testing (default: 8023)
- `claude.model` - Claude model to use (default: "claude-3-5-sonnet-20241022")
- `rate_limits` - Query limits per callsign per hour/day

## Architecture Overview

### Core Components

**Main Application** (`main.py`)
- `PacketClaude` class orchestrates all components
- Handles both AX.25 (via KISS/Direwolf) and telnet connections
- Routes incoming messages to Claude API with tool support
- Manages connection lifecycle and session state

**AX.25 Protocol Stack** (`ax25/`)
- `kiss.py` - KISS protocol client for Direwolf TNC communication
- `protocol.py` - AX.25 frame parsing and construction
- `connection.py` - AX25ConnectionHandler manages multiple simultaneous connections
- `yapp.py` - YAPP file transfer protocol implementation

**Claude Integration** (`claude/`)
- `client.py` - ClaudeClient wraps Anthropic API with tool support
- `session.py` - SessionManager maintains per-callsign conversation context

**Database & Persistence** (`database.py`)
- SQLite database for activity logs, rate limits, messages, files, chat channels, games
- Schema includes: connections, queries, rate_limits, messages, files, chat_messages, chat_channels, game_scores, etc.
- Database path: `data/sessions.db`

**Claude Tools** (`tools/`)
- Each tool provides a capability Claude can invoke
- `bbs_session.py` - BBS system control (session info, user list, help)
- `web_search.py` - Web search via DDGS
- `pota_spots.py` - Parks on the Air activations
- `dx_cluster.py` - DX cluster spots lookup
- `qrz_tool.py` - QRZ.com callsign lookup
- `message_tool.py` - Inter-user messaging system
- `file_tool.py` - File storage and sharing
- `chat_tool.py` - Multi-user chat channels
- `band_conditions.py` - HF propagation conditions

**Radio Control** (`radio/`)
- `hamlib_control.py` - PTT control via Hamlib (optional, graceful fallback if unavailable)

**Authentication & Limits** (`auth/`)
- `rate_limiter.py` - Per-callsign query rate limiting
- `qrz_lookup.py` - Callsign validation via QRZ.com

**File Transfer** (`files/`)
- `manager.py` - FileManager handles file storage, access control, size limits
- Files stored in database with metadata (owner, access level, size)
- YAPP protocol used for AX.25 transfers

### Connection Flow

1. **AX.25**: User connects via radio → Direwolf TNC → KISS TCP → PacketClaude
2. **Telnet**: User connects via telnet → TelnetServer → PacketClaude
3. PacketClaude creates/retrieves session for callsign
4. Messages routed to ClaudeClient with tools
5. Claude responses sent back over same connection
6. All activity logged to database

### BBS Commands

Users can issue special commands starting with `/`:
- `/help` - Show help
- `/status` - Show rate limits and session info
- `/clear` - Clear conversation history
- `/who` - List connected users
- `/files [public|private|mine]` - List files
- `/download <id>` - Download file via YAPP
- `/fileinfo <id>` - Show file metadata
- `/mail` - Check messages
- `/chat <channel>` - Join chat channel
- And more (see `main.py` command handlers)

### System Prompt

The system prompt for Claude is loaded from the file specified in `config.yaml` under `claude.system_prompt_file` (default: `config/system_prompt.txt`). This prompt instructs Claude on how to behave as a packet radio BBS operator, including:
- Keeping responses concise for low-bandwidth radio
- Using tools appropriately
- Ham radio etiquette and terminology
- BBS-style command syntax

## Code Organization Patterns

### Tool Pattern
All Claude tools follow this structure:
1. Initialize with reference to PacketClaude app
2. Implement `get_tool_definition()` returning tool schema
3. Implement `execute(action, params)` for tool invocation
4. Use database for persistence when needed

### Connection Handlers
Both AX25Connection and TelnetConnection share similar interfaces:
- `remote_address` property for callsign identification
- Connection state tracking
- Packet/message counters
- Activity timestamps

### Database Access
All database operations use context managers from `Database` class:
- `_get_connection()` provides transaction safety
- Row factory returns dict-like Row objects
- Schema auto-initialization on first run

## Testing Modes

**Telnet-only mode** is ideal for development without radio hardware:
```bash
python -m src.packetclaude.main --telnet-only
telnet localhost 8023
```

When testing telnet, you'll be prompted to enter your callsign. Use a valid amateur radio callsign format (e.g., "N0CALL" or "N0CALL-1").

## Common Development Tasks

### Adding a New Claude Tool
1. Create new file in `src/packetclaude/tools/`
2. Implement `get_tool_definition()` and `execute()` methods
3. Import and instantiate in `main.py` PacketClaude.__init__
4. Add to tools list passed to ClaudeClient

### Modifying Database Schema
1. Update `database.py` `_init_schema()` method
2. For existing databases, consider adding migration logic
3. Delete `data/sessions.db` to recreate from scratch (loses data)

### Adjusting Rate Limits
Edit `config/config.yaml` under `rate_limits` section

### Changing Response Length
- `claude.max_tokens` - Claude API token limit
- `rate_limits.max_response_chars` - Character limit for packet radio bandwidth conservation
