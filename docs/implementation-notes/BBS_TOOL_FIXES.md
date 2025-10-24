# BBS Tool and Logging Fixes

## Issues Found

### 1. BBS Tool Not Working
**Symptom**: Claude responded with "I apologize, but I'm currently experiencing an issue accessing the BBS session information."

**Root Cause**: The BBS tool had an `execute()` method but Claude's tool execution system looks for `execute_tool()`.

**Files affected**: Other tools (POTA, Web Search) had the correct `execute_tool()` method, but BBS tool was missing it.

### 2. DEBUG Logging Not Working
**Symptom**: Despite `LOG_LEVEL=DEBUG` in `.env`, no DEBUG messages appeared in logs.

**Root Cause**: The log level was hardcoded to `"INFO"` in `main.py` instead of reading from environment or config.

## Fixes Applied

### Fix 1: Added execute_tool() Method to BBS Tool

**File**: `src/packetclaude/tools/bbs_session.py`

Added the required `execute_tool()` wrapper method:

```python
def execute_tool(self, tool_name: str, tool_input: Dict) -> str:
    """
    Execute tool call from Claude

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool

    Returns:
        Tool result as string
    """
    if tool_name == "bbs_session":
        action = tool_input.get("action")
        connection_id = tool_input.get("connection_id")
        callsign = tool_input.get("callsign")
        return self.execute(action=action, connection_id=connection_id, callsign=callsign)
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
```

This wraps the existing `execute()` method and provides the interface Claude expects.

### Fix 2: Log Level Configuration

**File**: `src/packetclaude/config.py`

Added `log_level` property that checks environment first, then config:

```python
@property
def log_level(self) -> str:
    """Get log level"""
    # Check environment variable first, then config, then default
    import os
    env_level = os.getenv('LOG_LEVEL')
    if env_level:
        return env_level.upper()
    return self.get('logging.level', 'INFO').upper()
```

**File**: `src/packetclaude/main.py`

Changed from hardcoded to dynamic:

```python
# Before:
setup_logging(
    self.config.log_dir,
    log_level="INFO",  # Hardcoded!
    log_format=self.config.log_format,
    console_output=True
)

# After:
setup_logging(
    self.config.log_dir,
    log_level=self.config.log_level,  # Dynamic!
    log_format=self.config.log_format,
    console_output=True
)
```

**File**: `config/config.yaml`

Added log level configuration:

```yaml
logging:
  # Log directory
  log_dir: "logs"

  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  # Can be overridden with LOG_LEVEL environment variable
  level: "INFO"

  # ... rest of config
```

### Fix 3: Connection Context for Claude

**File**: `src/packetclaude/main.py`

Added connection context to messages sent to Claude so it knows which connection is making the request:

```python
# Add connection context to message for tool use
# This helps Claude know which connection is making the request
connection_type = "telnet" if isinstance(connection, TelnetConnection) else "ax25"
message_with_context = f"[Connection: {connection.remote_address} via {connection_type}] {message}"

# Query Claude
response_text, tokens_used, error = self.claude_client.send_message(
    message_with_context,
    history
)
```

Now when Claude uses the BBS tool, it knows the connection_id from the message context.

### Fix 4: Updated Tests

**File**: `scripts/test_bbs_tool.py`

Updated all test calls from `execute()` to `execute_tool()`:

```python
# Before:
result = tool.execute(action="get_help")

# After:
result = tool.execute_tool("bbs_session", {"action": "get_help"})
```

All tests now pass! ✓

## How Logging Now Works

1. **Environment variable** (highest priority): `LOG_LEVEL=DEBUG` in `.env`
2. **Config file**: `logging.level: "INFO"` in `config/config.yaml`
3. **Default**: `"INFO"` if neither is set

Priority order: Environment > Config > Default

## How BBS Tool Now Works

```
User types: "show me my session info"
    ↓
Message sent to Claude with context:
"[Connection: K0ASM via telnet] show me my session info"
    ↓
Claude analyzes intent → decides to use bbs_session tool
    ↓
Claude calls: execute_tool("bbs_session", {
    "action": "get_session_info",
    "connection_id": "K0ASM"  # Extracted from context
})
    ↓
Tool finds K0ASM in session manager and connections
    ↓
Returns JSON with session info
    ↓
Claude formats into natural response:
"You're connected as K0ASM via telnet..."
```

## Testing

### Test BBS Tool

```bash
python scripts/test_bbs_tool.py
```

Expected output:
```
✓ Tool definition is valid
✓ get_help works correctly
✓ get_status works correctly
✓ get_session_info works correctly
✓ list_users works correctly
✓ clear_history works correctly

All unit tests passed!
```

### Test Logging Level

```bash
# Set DEBUG level
export LOG_LEVEL=DEBUG

# Or in .env:
echo "LOG_LEVEL=DEBUG" >> .env

# Start PacketClaude
./packetclaude.py --telnet-only

# Check logs for DEBUG messages
tail -f logs/packetclaude_*.log | grep DEBUG
```

You should now see DEBUG level messages like:
```
"level": "DEBUG",
"message": "BBS session tool: action=get_status, connection=K0ASM, callsign=None"
```

### Test BBS Tool with Live System

```bash
# Terminal 1: Start PacketClaude with DEBUG logging
LOG_LEVEL=DEBUG ./packetclaude.py --telnet-only

# Terminal 2: Connect
telnet localhost 8023

# Try BBS commands:
> show me my session info
> who else is connected?
> what's the system status?
```

## Files Modified

1. `src/packetclaude/tools/bbs_session.py` - Added `execute_tool()` method
2. `src/packetclaude/config.py` - Added `log_level` property
3. `src/packetclaude/main.py` - Use `config.log_level` + add connection context
4. `config/config.yaml` - Added `logging.level` configuration
5. `scripts/test_bbs_tool.py` - Updated tests to use `execute_tool()`

## Before vs After

### Before

```
User: "show me my session info"
Claude: "I apologize, but I'm currently experiencing an issue accessing the BBS session information."

Logs: Only INFO level messages, no DEBUG
```

### After

```
User: "show me my session info"
Claude: "You're connected as K0ASM via telnet. Your session has been active for 2 minutes with 3 messages exchanged..."

Logs (with LOG_LEVEL=DEBUG):
DEBUG - BBS session tool: action=get_session_info, connection=K0ASM, callsign=None
DEBUG - Executing tool: bbs_session with input: {'action': 'get_session_info', 'connection_id': 'K0ASM'}
DEBUG - Found session for K0ASM: 3 messages, 2 queries
```

## Summary

✅ **BBS tool now works** - Added missing `execute_tool()` method
✅ **DEBUG logging works** - Reads `LOG_LEVEL` from environment/config
✅ **Connection context** - Claude knows which user is making requests
✅ **All tests pass** - Updated and validated

The BBS tool is now fully functional and Claude can help users with session management, system status, and BBS operations!
