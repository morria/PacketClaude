# Multi-User Chat System Documentation

## Overview

PacketClaude includes a real-time multi-user chat system inspired by classic BBS chat systems like CB Simulator (WWIV) and conference mode. Users can join channels to communicate in real-time with other operators currently connected to the BBS.

## Features

- **Multiple channels**: Users can join different channels for different topics
- **MAIN channel**: Default public channel created at startup
- **User presence tracking**: See who's online in each channel
- **Message history**: Last 4 messages from past 24 hours shown when joining
- **Custom channels**: Users can create channels by joining them
- **Bandwidth optimized**: Compressed output for packet radio
- **Classic BBS feel**: IRC-style /commands familiar to BBS users

## Architecture

### Database Schema

**chat_channels table:**
- `id`: Channel ID (primary key)
- `channel_name`: Uppercase channel name (unique)
- `created_by`: Callsign that created the channel
- `topic`: Channel topic/description
- `is_public`: Public flag (currently all channels are public)
- `created_at`: Timestamp

**chat_messages table:**
- `id`: Message ID (primary key)
- `channel_id`: Foreign key to chat_channels
- `callsign`: Sender callsign
- `message`: Message text
- `timestamp`: When message was sent

**chat_presence table:**
- `id`: Presence ID (primary key)
- `channel_id`: Foreign key to chat_channels
- `callsign`: User callsign
- `joined_at`: When user joined
- `last_seen`: Last activity timestamp
- `UNIQUE(channel_id, callsign)`: One presence per user per channel

### Components

**Database Methods** (`src/packetclaude/database.py`):
- `get_or_create_channel()`: Get existing or create new channel
- `list_channels()`: List all channels with user counts
- `join_channel()`: Add user to channel
- `leave_channel()`: Remove user from channel
- `leave_all_channels()`: Remove user from all channels (on disconnect)
- `get_channel_users()`: Get list of users in a channel
- `get_user_channels()`: Get channels a user is in
- `post_chat_message()`: Post message to channel
- `get_recent_messages()`: Get recent messages from channel
- `get_channel_by_name()`: Look up channel by name
- `cleanup_stale_presence()`: Remove inactive users
- `set_channel_topic()`: Set channel topic
- `get_total_chat_users()`: Count unique users in chat

**Chat Tool** (`src/packetclaude/tools/chat_tool.py`):
Claude API tool interface for chat operations:
- `join`: Join a channel (returns recent messages and user list)
- `leave`: Leave a channel
- `send`: Send message to channel
- `list_channels`: List all channels
- `who`: List users in a channel
- `recent`: Get recent messages
- `topic`: Set channel topic

## User Commands

### Basic Commands

- `/C` or `/CHAT` - Join MAIN channel
- `/JOIN [channel]` - Join or create a channel
- `/LEAVE [channel]` - Leave a specific channel
- `/LEAVE` - Leave current channel
- `/WHO [channel]` - List users in channel
- `/CHANNELS` or `/CH` - List all channels
- `/TOPIC [channel] [text]` - Set channel topic

### Natural Language

Claude understands flexible input:
- "chat" → Join MAIN
- "talk to others" → Join MAIN
- "who's online" → Show channels/users
- "join dx channel" → Join DX channel
- "leave" → Leave current channel

## Example Session

```
W2ASM-3> /chat
*** Joined #MAIN ***
Topic: Main public chat channel
3 users: W2ASM, K1ABC, N2DEF

Recent messages:
16:23 K1ABC> Anyone on 20m?
16:25 W2ASM> Quiet here, trying 17m
16:30 N2DEF> 73 all, QRT for dinner

Type your message, /WHO for users, /LEAVE to exit

W2ASM-3> hello everyone!
[#MAIN] W2ASM> hello everyone!

W2ASM-3> /who main
Users in #MAIN (3):
W2ASM
K1ABC
N2DEF

W2ASM-3> /join dx
*** Joined #DX ***
Topic: DX and contest discussion
0 users online

No recent messages

W2ASM-3> anyone working europe on 20m?
[#DX] W2ASM> anyone working europe on 20m?

W2ASM-3> /channels
Available channels:
#MAIN (3 users) - Main public chat channel
#DX (1 user) - DX and contest discussion
#TECH (0 users) - Technical topics

Type /JOIN [channel] to join

W2ASM-3> /leave dx
Left #DX

W2ASM-3>
```

## Message Format

Messages are displayed in ultra-compressed format for bandwidth efficiency:

```
HH:MM CALL> message text
```

Example:
```
16:30 W2ASM> Working K5XYZ on 14.260
16:31 K1ABC> Nice! Gud sigs here too
16:32 N2DEF> QRZ? Anyone on 20m SSB?
```

- Time in HH:MM format (5 chars)
- Callsign followed by >
- Message text
- No dates (assumed today)
- Total target: < 400 chars per display

## Channel Management

### Default Channels

The MAIN channel is created automatically at startup:
```python
self.database.get_or_create_channel("MAIN", "SYSOP", "Main public chat channel")
```

### Creating Channels

Users create channels by joining them:
```
/JOIN POTA
```

If channel doesn't exist, it's created automatically.

### Popular Channel Names

Suggested channel naming conventions:
- `MAIN` - Main public channel
- `DX` - DX and contest discussion
- `TECH` - Technical topics
- `POTA` - Parks on the Air
- `RAGCHEW` - Casual conversation
- `VHF` - VHF/UHF activity
- `QRP` - QRP operations
- `DIGITAL` - Digital modes
- `MOBILE` - Mobile operations
- `EMCOMM` - Emergency communications

## Presence Management

### Joining
When user joins a channel:
1. User added to chat_presence table
2. joined_at and last_seen timestamps set
3. Recent messages retrieved (last 4 from 24 hours)
4. User list retrieved
5. All displayed to user

### Leaving
User can leave by:
- `/LEAVE [channel]` - Leave specific channel
- `/LEAVE` - Leave current channel
- Disconnecting - Automatically leave all channels

### Cleanup
Stale presence is cleaned up automatically:
- Every 60 seconds in cleanup loop
- Removes users inactive > 1 hour
- `cleanup_stale_presence(hours=1)`

## Bandwidth Optimization

Chat system is optimized for 1200 baud packet radio:

### Join Message
```
*** Joined #MAIN ***
Topic: Main public chat channel
3 users: W2ASM, K1ABC, N2DEF

Recent messages:
16:23 K1ABC> Anyone on 20m?
16:25 W2ASM> Quiet here, trying 17m

Type your message, /WHO for users, /LEAVE to exit
```
Approximately 200 chars

### Channel List
```
Available channels:
#MAIN (5 users) - Main public chat channel
#DX (2 users) - DX and contest discussion
#TECH (1 user) - Technical topics
```
Approximately 150 chars

### Who List
```
Users in #MAIN (5):
W2ASM, K1ABC, N2DEF, W3XYZ, N4GHI
```
Approximately 60 chars

### Chat Messages
```
16:30 W2ASM> message here
```
Approximately 25 chars + message length

## Implementation Details

### Chat Tool Integration

The chat tool is registered with Claude in `main.py`:

```python
from .tools.chat_tool import ChatTool

chat_tool = ChatTool(database=self.database, enabled=True)
tools.append(chat_tool)
```

### System Prompt

Detailed chat instructions are in `config/system_prompt.txt` in the `<chat_system>` section:
- Command syntax
- Output formatting
- Natural language parsing
- Bandwidth optimization
- Classic BBS feel

### State Tracking

Claude tracks which channels a user has joined in the conversation context. This allows:
- Sending messages without /command when in a channel
- Context-aware responses
- Seamless switching between chat and normal queries

### Disconnect Handling

When user disconnects (`_on_disconnect` in `main.py`):
```python
self.database.leave_all_channels(connection.remote_address)
```

This ensures clean state - users don't appear online after disconnecting.

## Testing

### Manual Testing

1. Connect via telnet: `telnet localhost 8023`
2. Enter a callsign
3. Test commands:
   ```
   /chat
   hello world
   /who main
   /channels
   /join dx
   test message in dx
   /leave
   ```

### Multiple Users

Open multiple telnet sessions to test multi-user chat:

**Session 1 (W2ASM):**
```
/chat
hello everyone
```

**Session 2 (K1ABC):**
```
/chat
hi W2ASM!
```

Both should see each other's messages.

### Database Verification

Check database directly:
```bash
sqlite3 data/sessions.db

SELECT * FROM chat_channels;
SELECT * FROM chat_presence;
SELECT * FROM chat_messages ORDER BY timestamp DESC LIMIT 10;
```

## Classic BBS Inspiration

The chat system is inspired by these classic BBS chat systems:

### CB Simulator (WWIV)
- Multi-channel chat
- "CB" theme with /commands
- Real-time communication

### Conference Mode (Many BBSes)
- Topic-based channels
- User lists
- Message history

### IRC-style Commands
- `/join`, `/leave`, `/who`
- Channel names with #
- Simple command syntax

## Future Enhancements

Possible additions:
- Private messaging in chat (`/msg user message`)
- Channel moderators
- Private channels (password-protected)
- User ignore list
- Away status
- Longer message history option
- Chat logs/archives
- Channel announcements
- User colors/formatting (if terminals support)

## Bandwidth Considerations

At 1200 baud (typical VHF packet):
- ~120 characters per second
- 400 char message = ~3.3 seconds transmit
- Join message (200 chars) = ~1.7 seconds
- Chat message (50 chars) = ~0.4 seconds

Design keeps all outputs under 400 chars for reasonable response times on packet radio.

## Credits

Inspired by:
- CB Simulator (WWIV BBS software)
- Conference mode (various BBS systems)
- IRC (Internet Relay Chat)
- Classic packet radio chat systems

Implemented using Claude AI for natural language command parsing and intelligent chat moderation.
