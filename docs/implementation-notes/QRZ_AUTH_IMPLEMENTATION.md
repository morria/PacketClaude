# QRZ Authentication Implementation - In Progress

## What's Been Done

### 1. Created QRZ Lookup Client
**File**: `src/packetclaude/auth/qrz_lookup.py`

- XML API client for QRZ.com
- Session key management (24-hour validity)
- Callsign lookup with operator info extraction
- Callsign validation
- Graceful fallback when QRZ is disabled

### 2. Updated Session Management
**File**: `src/packetclaude/claude/session.py`

Added to `ConversationSession`:
- `authenticated` (bool) - Whether session is authenticated
- `operator_info` (Dict) - QRZ data (name, location, license class, etc.)
- `authenticate(operator_info)` - Method to mark session as authenticated

### 3. Configuration Updates
**File**: `src/packetclaude/config.py`

Added properties:
- `qrz_username` - Read from `QRZ_USERNAME` env var
- `qrz_password` - Read from `QRZ_PASSWORD` env var
- `qrz_enabled` - True if both credentials are provided

**File**: `.env.example`
```
QRZ_USERNAME=your_qrz_username
QRZ_PASSWORD=your_qrz_password
```

### 4. Main Application Updates
**File**: `src/packetclaude/main.py`

- Added `self.qrz_lookup` component
- Initialize QRZ lookup with credentials
- Modified `_on_connect()` to prompt for callsign if not authenticated

## What Still Needs to Be Done

### 1. Add `_authenticate_callsign()` Method

```python
def _authenticate_callsign(self, connection, callsign: str):
    """
    Authenticate a callsign via QRZ lookup

    Args:
        connection: The connection
        callsign: Callsign to authenticate
    """
    # Look up on QRZ
    operator_info = self.qrz_lookup.lookup(callsign)

    if operator_info is None:
        # Callsign not found or invalid
        self._send_to_station(connection,
            f"\\nCallsign {callsign} not found or invalid.\\n"
            "Please enter a valid amateur radio callsign: ")
        return

    # Get session and authenticate
    session = self.session_manager.get_session(connection.remote_address)
    session.authenticate(operator_info)

    # For telnet connections, update the callsign
    if isinstance(connection, TelnetConnection) and not connection.callsign:
        connection.set_callsign(callsign)
        # Update session manager key
        if connection._remote_address in self.session_manager.sessions:
            old_session = self.session_manager.sessions[connection._remote_address]
            del self.session_manager.sessions[connection._remote_address]
            self.session_manager.sessions[callsign.upper()] = old_session

    # Send welcome with operator info
    fullname = operator_info.get('fullname', '')
    location = operator_info.get('state', operator_info.get('country', ''))

    welcome = (
        f"\\nWelcome {fullname} ({callsign})!\\n"
        f"Location: {location}\\n\\n"
        f"{self.config.welcome_message}\\n"
    )
    self._send_to_station(connection, welcome)
```

### 2. Update `_on_data()` to Handle Auth Flow

```python
def _on_data(self, connection, data: bytes):
    """Handle incoming data from connection"""
    try:
        message = data.decode('utf-8', errors='ignore').strip()

        if not message:
            return

        # Check if session is authenticated
        session = self.session_manager.get_session(connection.remote_address)

        if not session.authenticated:
            # Treat message as callsign attempt
            callsign = message.upper().strip()

            # Basic format validation
            import re
            if not re.match(r'^[A-Z0-9]{1,2}[0-9][A-Z0-9]{1,4}(-[0-9]{1,2})?$', callsign):
                self._send_to_station(connection,
                    "\\nInvalid callsign format. Please enter a valid amateur radio callsign: ")
                return

            # Authenticate the callsign
            self._authenticate_callsign(connection, callsign)
            return

        # Rest of existing _on_data logic (help, quit, status, Claude query, etc.)
        logger.info(f"Message from {connection.remote_address}: {message}")

        # ... existing command handling ...
```

### 3. Add Dependencies

**File**: `requirements.txt`
```
requests>=2.31.0  # Already there for POTA
# QRZ uses standard library (xml.etree.ElementTree)
```

## Testing Plan

### 1. With QRZ Credentials

```bash
# Add to .env
QRZ_USERNAME=your_username
QRZ_PASSWORD=your_password

# Start PacketClaude
./packetclaude.py --telnet-only

# Connect without -l flag
telnet localhost 8023
```

Expected flow:
```
Welcome to PacketClaude!

Please enter your amateur radio callsign to continue: w1aw
```

System looks up W1AW on QRZ, then:
```
Welcome Hiram Percy Maxim (W1AW)!
Location: CT

Welcome to Packet Claude!
...
```

### 2. With Invalid Callsign

```
Please enter your amateur radio callsign to continue: INVALID

Callsign INVALID not found or invalid.
Please enter a valid amateur radio callsign:
```

### 3. With telnet -l

```bash
telnet -l w1aw localhost 8023
```

Expected: Immediate authentication (callsign detected from telnet protocol)
```
Welcome Hiram Percy Maxim (W1AW)!
Location: CT

Welcome to Packet Claude!
...
```

### 4. Without QRZ Credentials

If `QRZ_USERNAME` or `QRZ_PASSWORD` not set:
- Still prompts for callsign
- Does basic format validation only
- No QRZ lookup
- Welcome message without operator info

## Files Summary

**Created**:
- `src/packetclaude/auth/qrz_lookup.py` - QRZ API client

**Modified**:
- `src/packetclaude/claude/session.py` - Added auth fields
- `src/packetclaude/config.py` - Added QRZ config properties
- `src/packetclaude/main.py` - Added auth flow (in progress)
- `.env.example` - Added QRZ credentials

**Needs Completion**:
- `src/packetclaude/main.py` - Add `_authenticate_callsign()` method
- `src/packetclaude/main.py` - Update `_on_data()` to check authentication

## Benefits

1. **Security**: Only licensed hams can use the system
2. **Accountability**: Know who is using the system
3. **Personalization**: Greet users by name
4. **Context**: Claude knows user's location, license class, etc.
5. **Compliance**: Ensures only authorized users access the system

## Next Steps

1. Complete `_authenticate_callsign()` method implementation
2. Update `_on_data()` to enforce authentication
3. Test with real QRZ credentials
4. Test without QRZ credentials (format-only validation)
5. Document QRZ account requirements
