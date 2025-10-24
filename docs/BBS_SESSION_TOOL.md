# BBS Session Tool

The BBS Session Tool allows Claude to interact with the PacketClaude BBS system, providing session management, user information, and system control capabilities.

## Overview

Claude can now help users with BBS operations by using the `bbs_session` tool. This enables natural language interaction with system functions:

- **Get session information**: "Show me my session info"
- **List connected users**: "Who else is connected?"
- **System status**: "What's the system status?"
- **Clear history**: "Clear my conversation history"
- **Get help**: "What commands are available?"
- **Set callsign**: "Set my callsign to K0ASM"
- **Disconnect**: "I'm done, disconnect me"

## Features

### 1. Session Information

Claude can retrieve detailed session information for any connected user:

```
User: "Show me my session info"

Claude will retrieve:
- Callsign
- Message count
- Query count
- Connection time
- Last activity
- Idle time
- Connection type (AX.25 or telnet)
```

### 2. User Management

List all connected users and their status:

```
User: "Who else is connected?"

Claude will show:
- All connected users (AX.25 and telnet)
- Connection state
- Connection time
- Packet statistics
```

### 3. System Status

Get comprehensive system information:

```
User: "What's the system status?"

Claude will report:
- System name and version
- Enabled interfaces (AX.25, telnet)
- Connection counts
- Active sessions
- Total messages and queries
- Available tools (search, POTA)
```

### 4. Callsign Management

For telnet connections, Claude can get or set callsigns:

```
User: "Set my callsign to K0ASM"

Claude will:
- Update the telnet connection's callsign
- Update the connection identifier
- Maintain session continuity
```

### 5. Conversation History

Claude can clear conversation history:

```
User: "Clear my conversation history"

Claude will:
- Clear all messages from the session
- Maintain the session for future queries
- Confirm the action
```

### 6. Help Information

Claude can provide comprehensive help:

```
User: "What can I do here?"

Claude will show:
- Available BBS commands
- How to interact with Claude
- Available tools
- Usage notes
```

### 7. Disconnect Users

Claude can gracefully disconnect users:

```
User: "I'm done, disconnect me"

Claude will:
- Close the connection gracefully
- Clean up the session
- Log the disconnection
```

## Tool Actions

The BBS Session Tool supports these actions:

| Action | Description | Required Parameters |
|--------|-------------|-------------------|
| `get_session_info` | Get detailed session information | `connection_id` |
| `get_callsign` | Get callsign for a connection | `connection_id` |
| `set_callsign` | Set callsign (telnet only) | `connection_id`, `callsign` |
| `list_users` | List all connected users | none |
| `get_help` | Display help information | none |
| `get_status` | Show system status | none |
| `clear_history` | Clear conversation history | `connection_id` |
| `disconnect` | Disconnect a user | `connection_id` |

## Usage Examples

### Example 1: Session Information

**User**: "Show me my session info"

**Claude's Tool Call**:
```json
{
  "action": "get_session_info",
  "connection_id": "K0ASM"
}
```

**Tool Response**:
```json
{
  "success": true,
  "session": {
    "callsign": "K0ASM",
    "messages": 10,
    "queries": 5,
    "created_at": "2025-10-24T14:30:00",
    "last_activity": "2025-10-24T14:35:00",
    "idle_seconds": 30,
    "age_seconds": 300
  },
  "connection": {
    "type": "telnet",
    "callsign": "K0ASM",
    "state": "connected",
    "packets_sent": 5,
    "packets_received": 5
  }
}
```

**Claude's Response**: "You're connected as K0ASM via telnet. Your session has been active for 5 minutes with 10 messages exchanged (5 from you). You've been idle for 30 seconds. The connection is stable with 5 packets sent and received."

### Example 2: List Users

**User**: "Who else is connected?"

**Claude's Tool Call**:
```json
{
  "action": "list_users"
}
```

**Tool Response**:
```json
{
  "success": true,
  "total_users": 3,
  "users": [
    {
      "callsign": "K0ASM",
      "type": "telnet",
      "state": "connected",
      "connected_at": "2025-10-24T14:30:00"
    },
    {
      "callsign": "W1ABC",
      "type": "ax25",
      "state": "connected",
      "connected_at": "2025-10-24T14:25:00"
    },
    {
      "callsign": "127.0.0.1:54321",
      "type": "telnet",
      "state": "connected",
      "connected_at": "2025-10-24T14:32:00"
    }
  ]
}
```

**Claude's Response**: "There are 3 users currently connected:
1. K0ASM (you) - telnet connection since 14:30
2. W1ABC - packet radio (AX.25) connection since 14:25
3. 127.0.0.1:54321 - telnet connection since 14:32 (no callsign set)"

### Example 3: System Status

**User**: "What's the system status?"

**Claude's Tool Call**:
```json
{
  "action": "get_status"
}
```

**Tool Response**:
```json
{
  "success": true,
  "system": {
    "name": "PacketClaude",
    "description": "AX.25 Packet Radio Gateway for Claude AI",
    "version": "1.0"
  },
  "interfaces": {
    "ax25_enabled": true,
    "telnet_enabled": true,
    "ax25_connections": 1,
    "telnet_connections": 2,
    "total_connections": 3
  },
  "sessions": {
    "active_sessions": 3,
    "total_messages": 45,
    "total_queries": 20
  },
  "tools": {
    "web_search": true,
    "pota_spots": true
  }
}
```

**Claude's Response**: "PacketClaude v1.0 is running with both AX.25 packet radio and telnet interfaces enabled. Currently serving 3 connections (1 radio, 2 telnet) with 3 active conversation sessions. The system has processed 45 messages and 20 queries total. Available tools include web search and POTA spots lookup."

### Example 4: Set Callsign

**User**: "Set my callsign to K0ASM"

**Claude's Tool Call**:
```json
{
  "action": "set_callsign",
  "connection_id": "127.0.0.1:54321",
  "callsign": "K0ASM"
}
```

**Tool Response**:
```json
{
  "success": true,
  "message": "Callsign updated from 127.0.0.1:54321 to K0ASM",
  "old_callsign": "127.0.0.1:54321",
  "new_callsign": "K0ASM"
}
```

**Claude's Response**: "I've updated your callsign from 127.0.0.1:54321 to K0ASM. Your session will now be identified by your callsign instead of your IP address."

### Example 5: Clear History

**User**: "Clear my conversation history"

**Claude's Tool Call**:
```json
{
  "action": "clear_history",
  "connection_id": "K0ASM"
}
```

**Tool Response**:
```json
{
  "success": true,
  "message": "Conversation history cleared for K0ASM"
}
```

**Claude's Response**: "I've cleared your conversation history. We're starting fresh! How can I help you?"

## Integration

The BBS Session Tool is automatically enabled when PacketClaude starts. No configuration is required.

### Tool Initialization

The tool is initialized in `main.py` after the session manager:

```python
# Initialize BBS session tool
bbs_tool = BBSSessionTool(packetclaude_app=self)
tools.append(bbs_tool)
```

### Claude Integration

Claude automatically uses this tool when users ask about:
- Session information
- Connected users
- System status
- BBS operations
- Help and commands

Claude decides when to use the tool based on user intent.

## Testing

Run the unit tests:

```bash
python scripts/test_bbs_tool.py
```

Tests cover:
- Tool definition validity
- All 8 actions
- Error handling
- Session management
- Connection tracking

## How Claude Uses It

Claude doesn't expose the tool mechanics to users. Instead, it provides natural responses:

**Instead of**: "I'm calling the bbs_session tool with action get_status..."

**Claude says**: "Let me check the system status for you. PacketClaude v1.0 is running with..."

The tool is transparent to users - they just have natural conversations with Claude, who handles the BBS operations behind the scenes.

## Limitations

1. **set_callsign** only works for telnet connections (not AX.25)
2. **connection_id** must match an active connection
3. Tool requires session manager to be initialized
4. No authentication - assumes trusted users

## Security Considerations

The BBS Session Tool provides system control capabilities:

✅ **Safe operations**:
- Getting information (read-only)
- Clearing own history
- Setting own callsign

⚠️ **Privileged operations**:
- Disconnecting users
- Viewing all sessions

**Recommendation**: In production, add access control to limit who can perform privileged operations.

## Future Enhancements

Possible improvements:

1. **User roles**: Admin vs regular user capabilities
2. **Authentication**: Verify callsign ownership
3. **Message sending**: Let Claude send messages to other users
4. **Bulletin system**: Post/read bulletins
5. **File transfers**: Manage file uploads/downloads
6. **Statistics**: Detailed usage reports
7. **Ban management**: Block abusive users

## See Also

- [Session Management](../src/packetclaude/claude/session.py) - Conversation sessions
- [Web Search Tool](SEARCH_FEATURE.md) - Internet search capability
- [POTA Tool](POTA_TOOL.md) - Parks on the Air spots
- [Telnet Login](TELNET_LOGIN.md) - Automatic callsign detection

## Example Session

Here's a complete example session showing Claude using the BBS tool:

```
User: hello!

Claude: Hello! Welcome to PacketClaude. I'm Claude, an AI assistant
running on this packet radio BBS. How can I help you today?

User: who am I?

Claude: [uses get_session_info tool]
You're connected as 127.0.0.1:54321 via telnet. This is your first
message in this session, which just started a few seconds ago.

User: can you set my callsign to K0ASM?

Claude: [uses set_callsign tool]
Done! I've updated your callsign from 127.0.0.1:54321 to K0ASM.
Your session is now identified by your callsign.

User: who else is connected?

Claude: [uses list_users tool]
Right now it's just you (K0ASM) connected via telnet since 14:30.

User: what can this system do?

Claude: [uses get_help and get_status tools]
PacketClaude is an AI-powered packet radio BBS with several capabilities:

1. Natural conversation with me (Claude AI)
2. Web search - I can look up current information online
3. POTA spots - I can show you live Parks on the Air activations
4. Session management - track your conversation history

You can ask me questions about anything, request POTA spots on
specific bands, or get help with amateur radio topics. The system
supports both packet radio (AX.25) and telnet connections.

User: thanks! bye!

Claude: 73 de PacketClaude! Thanks for stopping by. Feel free to
connect again anytime! [Your connection will close automatically]
```

---

The BBS Session Tool makes PacketClaude feel like a real BBS with an intelligent sysop (Claude) who can help users navigate the system! 🎙️
