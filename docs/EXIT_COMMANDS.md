# Exit Commands in PacketClaude

PacketClaude supports multiple exit commands to allow users to disconnect from the BBS in various ways that are familiar to both packet radio and general computer users.

## Supported Exit Commands

Users can disconnect by typing any of the following commands:

- **`quit`** - Standard Unix exit command
- **`bye`** - Traditional BBS exit command
- **`exit`** - Common exit command
- **`73`** - Amateur radio goodbye (best regards)
- **`/exit`** - Slash command style
- **`close`** - Close connection
- **`logout`** - Logout command
- **`disconnect`** - Explicit disconnect
- **Ctrl-C** - Interrupt signal (terminal only)

## Behavior

When a user types any of these commands:

1. System responds with: `73! Goodbye.`
2. Connection is immediately closed
3. Session is ended (no context preservation)
4. User is disconnected from the BBS

## Natural Language Understanding

Claude AI is also configured to understand when users express intent to leave through natural language:

- "I want to exit"
- "I'm done"
- "Goodbye"
- "I need to go"
- "How do I leave?"

When Claude detects exit intent, it will politely inform the user of the available exit commands rather than actually disconnecting them. This gives users control over when they actually disconnect.

## Example Interactions

### Direct Command
```
User: quit
System: 73! Goodbye.
[Connection closed]
```

### Natural Language
```
User: How do I exit?
Claude: To disconnect from the BBS, you can type any of these commands:
        quit, bye, exit, 73, /exit, close, or press Ctrl-C

        73!
```

### Amateur Radio Style
```
User: 73
System: 73! Goodbye.
[Connection closed]
```

## Implementation Details

### Command Processing

Exit commands are processed at the highest priority in `main.py`:

```python
elif message.lower() in ['quit', 'bye', 'exit', '73', '/exit', 'close', 'logout', 'disconnect']:
    self._send_to_station(connection, "73! Goodbye.\n")
    # Disconnect based on connection type
    if isinstance(connection, TelnetConnection):
        self.telnet_server.disconnect(connection)
    else:
        self.connection_handler.disconnect(connection)
    return
```

These commands are handled BEFORE:
- Rate limiting checks
- Claude AI processing
- Tool execution

This ensures:
- Fast disconnection
- No token usage for exit
- Immediate response

### System Prompt

Claude's system prompt includes guidance:

```
When users want to disconnect or exit (saying things like "goodbye", "73",
"bye", "I'm done", "exit", "quit", etc.), politely inform them they can
disconnect by typing: quit, bye, exit, 73, /exit, close, or pressing Ctrl-C.
```

## Help Text

The help command shows all exit options:

```
User: help
System: PacketClaude Help:
        - Simply type your questions to chat with Claude AI
        - 'help' or '?' - Show this help
        - 'status' - Show rate limit status
        - 'clear' - Clear conversation history
        - Exit: 'quit', 'bye', 'exit', '73', '/exit', 'close', or Ctrl-C

        Commands:
        - Check mail, send messages, list sent messages
        - Look up callsigns, get POTA spots, search the web

        Your conversation context is preserved during the session.
```

## Welcome Message

The welcome message also mentions exit commands:

```
Welcome to Packet Claude!
You are now connected to Claude AI. Just type and press Enter.
Type 'help' for commands. To exit: quit, bye, exit, 73, or Ctrl-C
```

## Rationale

Multiple exit commands are supported because:

1. **Amateur Radio Culture**: "73" is the traditional amateur radio goodbye
2. **BBS Tradition**: "bye" was standard on classic BBSes
3. **Unix Convention**: "quit" and "exit" are familiar to Unix users
4. **Modern Conventions**: "/exit" follows modern command syntax
5. **Accessibility**: More options means easier to remember at least one
6. **User Expectations**: Different users expect different commands

## Testing

To test exit commands:

```bash
# Connect via telnet
telnet localhost 8023

# Try each command:
quit
bye
exit
73
/exit
close
logout
disconnect
```

Each should result in immediate disconnection with "73! Goodbye." message.

## See Also

- [BBS Session Tool](BBS_SESSION_TOOL_FEATURE.md) - System management
- [Quick Start Guide](../QUICK_START.md) - Getting started
- [Configuration](../config/config.yaml) - System configuration

---

**Note**: Exit commands are case-insensitive. `QUIT`, `Quit`, and `quit` all work the same way.
