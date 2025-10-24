# PacketClaude Messaging System

PacketClaude includes a complete BBS-style messaging system that allows amateur radio operators to send and receive messages to each other through the system.

## Overview

The messaging system provides:
- **Send messages** to other callsigns
- **Receive messages** from other users
- **List messages** (all or unread only)
- **Read messages** with automatic read tracking
- **Delete messages** (soft delete - messages retained in database)
- **Reply to messages** with automatic subject handling
- **Message notifications** when new mail arrives

## Features

### Message Structure

Each message contains:
- **From**: Sender's callsign
- **To**: Recipient's callsign
- **Subject**: Message subject (auto-generated from body if not provided)
- **Body**: Message content
- **Date**: Timestamp when sent
- **Read status**: Whether recipient has read the message
- **Reply tracking**: Messages can be linked as replies to previous messages

### Natural Language Interface

Users interact with the messaging system through natural language via Claude:

```
User: Check my mail
Claude: [Uses messages tool to list messages]
        You have 2 unread messages:
        1. N W1AW      Test message       2025-10-24 14:30
        2. N K1TTT     Hello from CT       2025-10-24 15:45

User: Read message 1
Claude: [Uses messages tool to read and mark as read]
        From: W1AW
        Date: 2025-10-24 14:30
        Subject: Test message

        This is a test message for the new BBS system.

User: Send a message to W2XYZ saying hello
Claude: [Uses messages tool to send]
        Message sent to W2XYZ.
```

## Usage Examples

### Listing Messages

**Received messages (all):**
```
User: Show my messages
User: List mail
User: Check messages
```

**Received messages (unread only):**
```
User: Show unread messages
User: Any new mail?
User: Check new messages
```

**Sent messages:**
```
User: Show my sent messages
User: List messages I sent
User: Show outbox
```

### Reading Messages

```
User: Read message 5
User: Show me message number 3
User: Open mail 1
```

Messages are automatically marked as read when opened.

### Sending Messages

**With explicit subject:**
```
User: Send a message to K1ABC
      Subject: QSO Request
      Body: Would you be available for a 20m QSO tomorrow at 1400Z?
```

**Without subject (auto-generated):**
```
User: Send mail to W1XYZ saying "Thanks for the contact yesterday!"
```

Subject will be generated as: "Thanks for the contact yesterday!"

### Replying to Messages

```
User: Reply to message 3 with "Sounds good, I'll be on 14.250 MHz"
```

The system automatically:
- Determines the recipient (original sender)
- Adds "Re: " prefix to subject
- Links the reply to the original message

### Deleting Messages

```
User: Delete message 2
User: Remove mail 5
```

Messages are soft-deleted (marked as deleted but retained in database).

## BBS-Style Display

Claude formats messages in a terse, BBS-style format:

### Message List (Received)
```
You have 3 messages (2 unread):

 # St From       Subject                    Date
 1 N  W1AW      Test message               2025-10-24 14:30
 2 N  K1TTT     Hello from CT              2025-10-24 15:45
 3    W2ASM     Re: QSO Request            2025-10-24 16:20

N = New (unread)
```

### Message List (Sent)
```
You have 2 sent messages:

 # St To         Subject                    Date
 1 R  K1ABC     QSO Request                2025-10-24 13:15
 2    W1AW      Thanks for contact         2025-10-24 14:00

R = Read by recipient
```

### Message Display
```
Message #1

From: W1AW
To: W2ASM
Date: 2025-10-24 14:30
Subject: Test message

This is a test message for the new BBS system.
Looking forward to working you on the air!

73,
Hiram
```

## Technical Implementation

### Database Schema

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_callsign TEXT NOT NULL,
    to_callsign TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    in_reply_to INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    deleted_at TIMESTAMP,
    FOREIGN KEY (in_reply_to) REFERENCES messages(id)
);
```

### Indexes

For performance, indexes are created on:
- `to_callsign` - Fast recipient lookups
- `from_callsign` - Fast sender lookups
- `created_at` - Fast chronological sorting

### API Functions

**Database Methods** (`src/packetclaude/database.py`):
- `send_message(from, to, subject, body, in_reply_to)` - Send a message
- `get_messages(callsign, unread_only, include_deleted)` - List received messages
- `get_sent_messages(callsign)` - List sent messages
- `get_message(message_id, callsign)` - Get specific message
- `mark_message_read(message_id, callsign)` - Mark as read
- `delete_message(message_id, callsign)` - Soft delete message
- `get_unread_count(callsign)` - Count unread messages

**Message Tool** (`src/packetclaude/tools/message_tool.py`):
- Provides Claude tool interface
- Formats BBS-style responses
- Handles all message operations
- Generates subjects from body when needed

## Privacy & Security

### Access Control

- Users can only read messages sent TO or FROM their callsign
- Users can only delete their own received messages
- Users cannot modify other users' messages
- Deleted messages are soft-deleted (retained for auditing)

### Data Storage

- All messages stored in SQLite database
- Timestamps in UTC
- Soft deletes preserve message history
- No automatic expiration (manual cleanup possible)

### Message Content

- No size limits on message body
- Subjects auto-generated if not provided
- All text content (no attachments)
- UTF-8 encoding supported

## Administration

### Database Location

Messages stored in: `data/sessions.db`

Table: `messages`

### Viewing All Messages (SQL)

```sql
SELECT id, from_callsign, to_callsign, subject, created_at, is_read
FROM messages
WHERE deleted_at IS NULL
ORDER BY created_at DESC;
```

### Cleanup Old Messages

```sql
-- Delete messages older than 90 days
DELETE FROM messages
WHERE created_at < datetime('now', '-90 days');
```

### Message Statistics

```sql
-- Total messages
SELECT COUNT(*) FROM messages WHERE deleted_at IS NULL;

-- Messages by user
SELECT to_callsign, COUNT(*) as count
FROM messages
WHERE deleted_at IS NULL
GROUP BY to_callsign
ORDER BY count DESC;

-- Unread message count
SELECT COUNT(*) FROM messages
WHERE is_read = 0 AND deleted_at IS NULL;
```

## Future Enhancements

Possible improvements:

1. **Bulletin Messages** - Send to "ALL" for public announcements
2. **Message Attachments** - Support for file attachments
3. **Message Forwarding** - Forward messages to other users
4. **Message Export** - Export messages to text/JSON
5. **Message Search** - Search by subject, sender, keywords
6. **Message Threading** - Visual display of conversation threads
7. **Message Expiration** - Auto-delete old messages
8. **Read Receipts** - Notify sender when message is read
9. **Message Priority** - Urgent/normal/low priority levels
10. **Draft Messages** - Save messages before sending

## Troubleshooting

### "Message not found"

**Cause**: Message ID doesn't exist or user doesn't have permission

**Fix**: Verify message ID and that you're the sender or recipient

### "Failed to send message"

**Causes**:
1. Database connection error
2. Invalid callsign format
3. Missing required fields

**Fix**: Check logs for details

### Messages not appearing

**Cause**: Looking at wrong callsign

**Fix**: Messages are sent TO specific callsigns. Check the recipient callsign.

### Can't delete message

**Cause**: Only recipients can delete messages they received

**Fix**: You can only delete messages sent TO you, not FROM you

## Examples

### Basic Workflow

```
1. User connects to BBS
2. System: "Welcome! You have 2 new messages."
3. User: "Check mail"
4. System: Lists unread messages
5. User: "Read message 1"
6. System: Displays message, marks as read
7. User: "Reply with: Thanks for the info!"
8. System: Sends reply
```

### Sending to Multiple Users

```
User: Send a message to W1AW saying "CQ POTA K-1234"
Claude: Message sent to W1AW.

User: Send the same message to K1TTT
Claude: Message sent to K1TTT.
```

### Managing Inbox

```
User: Show unread messages
Claude: You have 5 unread messages...

User: Read message 1
User: Read message 2
User: Delete message 3
User: Reply to message 4 with "..."

User: Show unread messages
Claude: You have 2 unread messages...
```

## See Also

- [BBS Session Tool](BBS_SESSION_TOOL_FEATURE.md) - System management
- [Database Schema](../src/packetclaude/database.py) - Database structure
- [Message Tool](../src/packetclaude/tools/message_tool.py) - Tool implementation

---

**Note**: The messaging system is always enabled and available to all authenticated users.
