# File Transfer via AX.25 with YAPP Protocol

PacketClaude supports file upload and download over AX.25 packet radio connections using the YAPP (Yet Another Packet Protocol) standard. This document explains how to use file transfer features with the Packet Commander iOS app or other YAPP-capable software.

## Overview

The file transfer feature allows users to:
- **Upload files** to PacketClaude via AX.25
- **Download files** from PacketClaude via AX.25
- **Share files** with specific callsigns or make them public
- **Manage files** through simple commands or by asking Claude

## Supported Protocols

### YAPP (Yet Another Packet Protocol)

YAPP is a standard file transfer protocol used in amateur radio packet networks. It provides:
- Binary-safe file transfers
- Block-based transmission (128-byte blocks)
- Error detection with checksums
- Automatic retry on errors
- Progress tracking

## File Size and Storage Limits

- **Maximum file size:** 100 KB per file
- **Maximum files per user:** 50 files
- **Maximum total storage per user:** 5 MB

These limits ensure efficient use of packet radio bandwidth and storage resources.

## File Access Levels

Files can have three access levels:

1. **Private** (default): Only you can access the file
2. **Public**: Anyone can download the file
3. **Shared**: Specific callsigns you've shared with can access the file

## Using File Transfer Commands

### List Available Files

```
/files [filter]
```

Lists files you can access. Optional filters:
- `public` - Show only public files
- `private` - Show only your private files
- `shared` - Show only files shared with you
- No filter - Show all accessible files

**Example:**
```
/files public
```

### Upload a File

```
/upload
```

Initiates a file upload session. After typing this command:
1. Your YAPP-capable client (e.g., Packet Commander) will detect the upload session
2. Select the file to upload
3. The client will automatically transfer the file using YAPP
4. You'll receive a file ID when the upload completes

**Example:**
```
/upload
Ready to receive file via YAPP. Send ENQ to start.
[...transfer happens...]
File uploaded successfully!
File ID: 42
Filename: log.txt
Size: 2.5 KB
Use /publicfile 42 to make it public.
Use /share 42 <callsign> to share it.
>
```

### Download a File

```
/download <file_id>
```

Downloads a file by its ID. The file will be transferred using YAPP protocol.

**Example:**
```
/download 42
Starting download of log.txt...
[...transfer happens...]
Download complete!
>
```

### Get File Information

```
/fileinfo <file_id>
```

Shows detailed information about a file.

**Example:**
```
/fileinfo 42

File Information:
  ID: 42
  Filename: log.txt
  Size: 2.5 KB
  Owner: W1ABC
  Access: private
  Uploaded: 2025-11-06 10:30:00
  Downloads: 3
  Description: None
>
```

### Share a File with a Callsign

```
/share <file_id> <callsign>
```

Shares one of your files with a specific callsign.

**Example:**
```
/share 42 K2XYZ
File shared with K2XYZ.
>
```

### Make a File Public

```
/publicfile <file_id>
```

Makes one of your files accessible to everyone.

**Example:**
```
/publicfile 42
File 42 is now public.
>
```

### Delete a File

```
/deletefile <file_id>
```

Deletes one of your files (you must be the owner).

**Example:**
```
/deletefile 42
File 42 deleted.
>
```

## Using Packet Commander iOS App

[Packet Commander](https://apps.apple.com/app/packet-commander) is a YAPP-capable iOS app that works seamlessly with PacketClaude's file transfer features.

### Setup

1. **Connect to PacketClaude** via AX.25:
   ```
   connect N0CALL-10
   ```

2. **Authenticate** with your callsign if using telnet interface

### Uploading Files from Packet Commander

1. Type `/upload` in PacketClaude
2. Wait for the "Ready to receive" message
3. In Packet Commander, tap the upload button
4. Select your file (must be under 100 KB)
5. The app will automatically transfer using YAPP
6. Note the file ID provided when upload completes

### Downloading Files with Packet Commander

1. Type `/files` to see available files
2. Type `/download <file_id>` for the file you want
3. Packet Commander will automatically receive the file via YAPP
4. The file will be saved to your device

## Using Claude for File Management

You can ask Claude to help with file operations using natural language:

**Examples:**
- "Show me all public files"
- "What files do I have?"
- "Tell me about file 42"
- "Help me upload a file"
- "How do I share files?"

Claude will use the file management tool to provide information and guide you through operations.

## YAPP Protocol Details

### Transfer Process

**Upload (Receiving) Flow:**
```
1. User types /upload
2. PacketClaude sends ACK (ready to receive)
3. Client sends ENQ (request to send)
4. PacketClaude sends ACK
5. Client sends SOH + header (filename, size)
6. PacketClaude sends ACK
7. Client sends STX + data block (128 bytes)
8. PacketClaude sends ACK
9. Repeat steps 7-8 for each block
10. Client sends ETX (end of transfer)
11. PacketClaude sends final ACK
12. File is saved to database
```

**Download (Sending) Flow:**
```
1. User types /download <file_id>
2. PacketClaude sends ENQ (request to send)
3. Client sends ACK (ready to receive)
4. PacketClaude sends SOH + header
5. Client sends ACK
6. PacketClaude sends STX + data block
7. Client sends ACK
8. Repeat steps 6-7 for each block
9. PacketClaude sends ETX
10. Client sends final ACK
```

### Error Handling

- **NAK (Negative Acknowledge):** Packet will be retransmitted
- **Timeout:** Transfer will retry up to 3 times
- **CAN (Cancel):** Transfer will be aborted
- **Checksum errors:** Detected and retransmitted automatically

### Block Size and Performance

- **Block size:** 128 bytes
- **Typical transfer time at 1200 baud:** ~100 KB takes 10-15 minutes
- **Progress tracking:** Block numbers and completion percentage

## File Storage

Files are stored in the SQLite database as BLOBs:
- **Database location:** `data/sessions.db`
- **Table:** `files`
- **Metadata:** Filename, size, checksum, owner, access level, timestamps
- **Integrity:** MD5 checksums verify file integrity

## Troubleshooting

### Upload Fails

**Problem:** Upload times out or fails
**Solutions:**
- Ensure file is under 100 KB
- Check your packet radio connection quality
- Verify you haven't exceeded storage quota (5 MB total)
- Try uploading again - retries are automatic

### Download Fails

**Problem:** Download times out or fails
**Solutions:**
- Verify the file ID is correct with `/fileinfo <id>`
- Check you have access to the file
- Ensure stable packet radio connection
- Use `/download <id>` again to restart

### Access Denied

**Problem:** "Access denied" when downloading
**Solutions:**
- File may be private - ask owner to share with you
- Use `/files public` to see public files only
- Ask owner to use `/share <file_id> <your_callsign>`

### File Not Found

**Problem:** "File not found" error
**Solutions:**
- Use `/files` to list available files
- File may have been deleted by owner
- Verify you have the correct file ID

### YAPP Not Working on Telnet

**Problem:** YAPP transfers don't work via telnet
**Reason:** YAPP protocol requires AX.25 binary data frames
**Solution:** Use Packet Commander or another AX.25 client for file transfers

## Configuration

File transfer settings in `config/config.yaml`:

```yaml
file_transfer:
  # Enable/disable file transfer
  enabled: true

  # Maximum file size (KB)
  max_file_size_kb: 100

  # Maximum files per user
  max_files_per_user: 50

  # Maximum storage per user (MB)
  max_total_size_per_user_mb: 5

  # YAPP timeout (seconds)
  yapp_timeout_seconds: 30
```

## Technical Implementation

### Components

1. **YAPP Protocol Handler** (`src/packetclaude/ax25/yapp.py`)
   - Implements YAPP packet structure
   - Manages transfer state machines
   - Handles retries and errors

2. **File Manager** (`src/packetclaude/files/manager.py`)
   - File validation and sanitization
   - Storage and retrieval
   - Access control checks
   - Quota enforcement

3. **Database Layer** (`src/packetclaude/database.py`)
   - File storage as BLOBs
   - Metadata management
   - Sharing relationships

4. **Connection Handler** (`src/packetclaude/ax25/connection.py`)
   - YAPP packet detection
   - Transfer coordination
   - Progress tracking

## Security Considerations

- **Filename Sanitization:** All filenames are sanitized to prevent directory traversal
- **Size Limits:** Prevent resource exhaustion
- **Access Control:** Files are private by default
- **Checksum Verification:** MD5 checksums ensure file integrity
- **Quota Enforcement:** Per-user limits prevent abuse

## Best Practices

1. **Keep files small:** Under 50 KB transfers faster and more reliably
2. **Use descriptive filenames:** Help others understand file contents
3. **Make useful files public:** Share information with the community
4. **Clean up old files:** Delete files you no longer need with `/deletefile`
5. **Compress before upload:** Zip or compress files to reduce size
6. **Test with small files first:** Verify your setup works with a small test file

## Examples

### Sharing a Contest Log

```
# Upload your log
/upload
[...upload log.txt...]
File ID: 123

# Make it public
/publicfile 123
File 123 is now public.

# Share with specific friends
/share 123 W1ABC
/share 123 K2XYZ
```

### Downloading a Frequency List

```
# List public files
/files public
ID  | Filename           | Size   | Owner    | Access
----|-------------------|--------|----------|--------
456 | frequencies.txt   | 5.2 KB | N0CALL   | public

# Get more info
/fileinfo 456
[...see details...]

# Download it
/download 456
[...transfer happens...]
```

### Collaborating on Documentation

```
# Check what files are shared with you
/files shared

# Download collaborator's file
/download 789

# Upload your updated version
/upload
[...upload updated.txt...]
File ID: 790

# Share back with them
/share 790 W1ABC
```

## See Also

- [Packet Commander on the App Store](https://apps.apple.com/app/packet-commander)
- [YAPP Protocol Specification](http://www.ka9q.net/papers/yapp.html)
- [AX.25 Protocol Specification](http://www.tapr.org/pdf/AX25.2.2.pdf)
- [PacketClaude Main README](../README.md)
