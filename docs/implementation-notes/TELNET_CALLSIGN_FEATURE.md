# Telnet Callsign Detection - Implementation Summary

## Feature Overview

PacketClaude now automatically detects and uses your callsign when you connect via telnet by reading environment variables sent by your telnet client.

## What Was Implemented

### 1. Telnet Protocol Support (RFC 1572)

**File**: `src/packetclaude/telnet/server.py`

Added support for telnet NEW-ENVIRON option:

- **Protocol constants** for IAC, WILL, DO, SB, SE commands
- **Environment variable parsing** to extract USER and LOGNAME
- **IAC sequence handling** to strip telnet protocol from data stream
- **Automatic callsign detection** when environment variables are received

### 2. Connection Identity Management

**Modified**: `TelnetConnection` class

- Added `callsign` property to store detected callsign
- Modified `remote_address` property to return callsign if detected, otherwise IP:port
- Added `set_callsign()` method to update callsign with logging
- Maintains backward compatibility with IP:port fallback

### 3. Protocol Flow

```
Client connects
    ↓
Server sends: IAC DO NEW-ENVIRON (request environment)
    ↓
Client responds: IAC SB NEW-ENVIRON IS VAR "USER" VALUE "K0ASM" IAC SE
    ↓
Server parses environment data
    ↓
Extracts USER or LOGNAME variable
    ↓
Sets connection.callsign = "K0ASM"
    ↓
All subsequent operations use callsign instead of IP:port
```

### 4. Key Features

✅ **Automatic detection** - No user action required beyond setting telnet environment
✅ **Graceful fallback** - Uses IP:port if no login name provided
✅ **Case normalization** - Converts callsigns to uppercase (K0ASM, not k0asm)
✅ **Protocol compliance** - Implements RFC 854 and RFC 1572
✅ **Transparent parsing** - Removes telnet protocol sequences from data stream
✅ **Connection tracking** - Updates connection dictionary key when callsign detected

## Code Changes

### New Constants

```python
# Telnet protocol constants (RFC 854, RFC 1572)
IAC = b'\xff'  # Interpret As Command
WILL = b'\xfb'
WONT = b'\xfc'
DO = b'\xfd'
DONT = b'\xfe'
SB = b'\xfa'  # Subnegotiation Begin
SE = b'\xf0'  # Subnegotiation End
TELOPT_NEW_ENVIRON = b'\x27'  # RFC 1572
```

### New Methods

**`TelnetConnection.set_callsign(callsign: str)`**
- Sets and validates callsign
- Converts to uppercase
- Logs the identification

**`TelnetServer._parse_telnet_data(conn, data) -> bytes`**
- Parses raw data from client
- Extracts IAC command sequences
- Handles subnegotiation (SB...SE)
- Returns clean data with protocol stripped

**`TelnetServer._parse_environ(conn, env_data)`**
- Parses NEW-ENVIRON subnegotiation data
- Extracts VAR and VALUE pairs
- Detects USER and LOGNAME variables
- Sets callsign on connection

### Modified Methods

**`TelnetServer._accept_loop()`**
- Sends IAC DO NEW-ENVIRON on new connection
- Requests environment variables from client

**`TelnetServer._receive_loop()`**
- Calls `_parse_telnet_data()` before processing
- Strips telnet protocol from incoming data

**`TelnetConnection.remote_address` property**
- Returns `callsign` if set
- Falls back to `IP:port` if not set

## Testing

### Unit Tests

**File**: `scripts/test_telnet_parsing.py`

Tests:
- ✅ Environment variable parsing (USER)
- ✅ Alternative variable (LOGNAME)
- ✅ Fallback to IP:port when no login
- ✅ Telnet protocol sequence parsing
- ✅ IAC command removal from data stream

All tests pass!

### Integration Tests

**File**: `scripts/test_telnet_login.py`

Tests:
- Connection with USER variable
- Connection without environment (fallback)
- Protocol negotiation with live server

Requires running PacketClaude server.

## Documentation

### New Documentation

**`docs/TELNET_LOGIN.md`** - Comprehensive guide covering:
- How it works
- Telnet client support (PuTTY, telnet, SecureCRT, etc.)
- Manual configuration methods
- Protocol details
- Verification steps
- Troubleshooting
- Security considerations
- Examples

### Updated Documentation

**`QUICK_START.md`**
- Added tip about automatic callsign detection
- Added link to TELNET_LOGIN.md
- Added feature to checklist

## How to Use

### Standard telnet (Linux/macOS)

```bash
# Uses your Unix username
telnet localhost 8023

# Or set custom callsign
USER=K0ASM telnet localhost 8023
```

### PuTTY (Windows)

1. Connection → Telnet → Environment
2. Add: `USER` = `K0ASM`
3. Connect

### Verification

After connecting, check logs:

```bash
tail -f logs/packetclaude_*.log | grep "identified as"
```

You should see:
```
Connection 127.0.0.1:54321 identified as K0ASM
```

## Benefits

1. **Ham radio convention** - Uses callsigns like packet radio
2. **Persistent identity** - Same callsign across connections
3. **Better rate limiting** - Rate limits per callsign, not IP
4. **Clearer logs** - See callsigns instead of IP addresses
5. **No extra configuration** - Works automatically with most telnet clients

## Backward Compatibility

✅ **Fully backward compatible**
- Existing connections still work
- IP:port used if no callsign detected
- Rate limiter accepts both formats
- No breaking changes to API

## Future Enhancements

Possible improvements:

1. **Custom variables** - Support CALLSIGN environment variable
2. **Login prompt** - Interactive callsign prompt if not provided
3. **Validation** - Verify callsign format (A1BC-12)
4. **Authentication** - Optional password/token verification
5. **Callsign database** - Lookup callsign info from FCC/RAC databases

## Security Notes

⚠️ **This is NOT authentication**
- Clients can send any value
- No verification of callsign ownership
- Assumes good faith (ham radio tradition)
- Rate limiting still prevents abuse

For production security:
- Add password authentication
- Use certificate-based auth
- Implement token verification
- Add callsign validation against official databases

## Summary

This feature brings PacketClaude closer to traditional packet radio behavior by using callsigns as the primary identifier for telnet connections. It's automatic, transparent, and maintains full backward compatibility while providing a more authentic ham radio experience.

**Lines of code**: ~150 lines (protocol parsing + environment extraction)
**Files modified**: 1 (`src/packetclaude/telnet/server.py`)
**Test files**: 2 (unit tests + integration tests)
**Documentation**: 1 comprehensive guide + updates to quick start

The implementation is clean, well-tested, and ready for use! 73 de PacketClaude 🎙️
