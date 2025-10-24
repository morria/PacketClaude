# QRZ.com Callsign Authentication

PacketClaude requires all users to authenticate with a valid amateur radio callsign before using the system. Callsigns are verified against QRZ.com's database to ensure only licensed operators access the BBS.

## Overview

When a user connects:
1. System prompts for callsign (unless detected via telnet `-l` flag)
2. User enters their callsign
3. System validates format
4. System looks up callsign on QRZ.com
5. If valid, user is authenticated and welcomed with their info
6. If invalid, user must try again

**Users cannot proceed without a valid callsign.**

## Setup

### 1. Get QRZ.com Account

You need a QRZ.com account to use the XML API:
1. Go to https://www.qrz.com/
2. Create a free account (or use existing account)

**For API Key (Optional - Enhanced Features)**:
3. Subscribe to XML Logbook Data Access ($39.95/year as of 2025)
4. Get your API key from https://www.qrz.com/docs/xml or your account settings
5. Note: You still need username/password; the API key enables additional features

**For Username/Password (Free)**:
3. Use your QRZ.com username and password (this works for basic lookups)

### 2. Add Credentials to .env

Edit your `.env` file:

**Required for all users:**
```bash
# Anthropic API Key
ANTHROPIC_API_KEY=your_api_key_here

# QRZ.com Username/Password (required)
QRZ_USERNAME=your_qrz_username
QRZ_PASSWORD=your_qrz_password

# Logging
LOG_LEVEL=INFO
```

**Optional - If you have XML Logbook subscription:**
```bash
# Add this in addition to username/password
QRZ_API_KEY=your_qrz_api_key
```

**Note**: The API key is optional and provides enhanced features if you have a paid XML Logbook subscription. Username and password are always required for authentication.

### 3. Restart PacketClaude

```bash
./packetclaude.py --telnet-only
```

You should see in the logs:
```
INFO - QRZ callsign lookup enabled
```

If credentials are missing:
```
WARNING - QRZ lookup disabled - no credentials provided
```

## User Experience

### With Telnet (No -l Flag)

```bash
$ telnet localhost 8023
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.

Welcome to PacketClaude!

Please enter your amateur radio callsign to continue: w1aw

Welcome Hiram Percy Maxim (W1AW)!
Location: CT
License: Extra

Welcome to Packet Claude!
You are now connected to Claude AI...
```

### With Telnet -l Flag

```bash
$ telnet -l w1aw localhost 8023
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.

Welcome Hiram Percy Maxim (W1AW)!
Location: CT
License: Extra

Welcome to Packet Claude!
You are now connected to Claude AI...
```

Authentication happens automatically!

### Invalid Callsign

```bash
Please enter your amateur radio callsign to continue: invalid

Callsign INVALID not found or invalid.
Please enter a valid amateur radio callsign:
```

### Wrong Format

```bash
Please enter your amateur radio callsign to continue: 123abc

Invalid callsign format. Please enter a valid amateur radio callsign:
```

## What Gets Stored

After successful authentication, the session stores:

```python
{
    'call': 'W1AW',
    'fname': 'Hiram Percy',
    'name': 'Maxim',
    'fullname': 'Hiram Percy Maxim',
    'addr1': '225 Main Street',
    'addr2': '',
    'state': 'CT',
    'zip': '06111',
    'country': 'United States',
    'lat': '41.7658',
    'lon': '-72.6734',
    'grid': 'FN31pr',
    'email': 'w1aw@arrl.org',
    'class': 'Extra',
    'expires': '2025-12-31',
    # ... and more
}
```

This information is:
- Stored in the session
- Available to Claude for context
- Used for personalized greetings
- Logged in the database

## Without QRZ Credentials

If you don't provide QRZ credentials, the system will:
- Still prompt for callsign
- Do basic format validation only
- **Not** look up operator info
- **Not** verify callsign exists
- Allow any properly-formatted callsign

This is useful for:
- Testing
- Development
- Running without internet
- Privacy concerns

But it means:
- No verification that user is licensed
- No operator information
- No personalized welcome

## Configuration

### Environment Variables

**API Key Method (Recommended)**:
```bash
QRZ_API_KEY=your_api_key  # Your QRZ.com API key
```

**Username/Password Method (Alternative)**:
```bash
QRZ_USERNAME=your_username  # Your QRZ.com username
QRZ_PASSWORD=your_password  # Your QRZ.com password
```

### Code Properties

```python
config.qrz_api_key   # From QRZ_API_KEY
config.qrz_username  # From QRZ_USERNAME
config.qrz_password  # From QRZ_PASSWORD
config.qrz_enabled   # True if API key OR username+password are set
```

## API Details

### QRZ.com XML API

PacketClaude uses the QRZ XML API (https://xmldata.qrz.com/xml/current/)

**API Key Authentication (Recommended)**:
```
GET ?key=your_api_key&callsign=W1AW
Returns: <Callsign><call>W1AW</call><fname>Hiram Percy</fname>...</Callsign>
```

- No session management needed
- Single-step lookup
- Direct authentication with each request
- Requires XML Logbook Data Access subscription

**Username/Password Authentication (Free)**:
```
Step 1: GET ?username=user&password=pass
Returns: <Session><Key>abc123</Key></Session>

Step 2: GET ?s=abc123&callsign=W1AW
Returns: <Callsign><call>W1AW</call><fname>Hiram Percy</fname>...</Callsign>
```

- Session keys valid for 24 hours
- Automatically refreshed when expired
- Cached for reuse across lookups

**Rate Limits**:
- QRZ.com limits API requests
- API key method supports higher limits
- System caches sessions (username/password) to minimize requests
- One lookup per user authentication

## Security & Privacy

### What's Sent to QRZ

- Your QRZ.com username/password (for session key)
- User's callsign (for lookup)

### What's NOT Sent

- User's messages
- Conversation content
- System logs
- Any other data

### QRZ Privacy

QRZ.com's XML API is read-only:
- No data is written to QRZ
- No profile changes
- Just lookup functionality

### Data Storage

Operator info is stored:
- In memory (session object)
- In SQLite database (sessions table)
- In logs (callsign only, not personal info)

Not stored outside the system.

## Troubleshooting

### "QRZ lookup disabled"

**Cause**: Missing QRZ credentials in `.env`

**Fix (API Key - Recommended)**:
```bash
echo "QRZ_API_KEY=your_api_key" >> .env
./packetclaude.py --telnet-only
```

**Fix (Username/Password - Free)**:
```bash
echo "QRZ_USERNAME=your_username" >> .env
echo "QRZ_PASSWORD=your_password" >> .env
./packetclaude.py --telnet-only
```

### "Callsign not found"

**Causes**:
1. Callsign doesn't exist in QRZ database
2. Typo in callsign
3. Callsign expired/cancelled
4. QRZ API down

**Fix**:
- Verify callsign on https://www.qrz.com/
- Check spelling
- Try again

### "QRZ authentication error"

**Causes**:
1. Wrong QRZ username/password
2. Account suspended
3. Network issues

**Check logs**:
```bash
tail -f logs/packetclaude_*.log | grep -i qrz
```

**Fix**:
- Verify credentials on QRZ.com
- Check network connection
- Check QRZ.com status

### Users Can't Login

**Cause**: QRZ API unavailable

**Temporary Fix**: Remove QRZ credentials from `.env` to disable lookup:
```bash
# Comment out in .env:
# QRZ_USERNAME=...
# QRZ_PASSWORD=...
```

Restart - system will use format-only validation.

## Developer Info

### Files

- `src/packetclaude/auth/qrz_lookup.py` - QRZ API client
- `src/packetclaude/claude/session.py` - Session authentication
- `src/packetclaude/main.py` - Authentication flow
- `src/packetclaude/config.py` - QRZ config

### Testing Without QRZ

For development/testing without real QRZ credentials:

```python
# In main.py, mock the lookup:
self.qrz_lookup.lookup = lambda callsign: {
    'call': callsign,
    'fullname': 'Test User',
    'state': 'XX',
    'class': 'Extra'
}
```

Or just omit QRZ credentials - system will accept any valid format.

### Custom Validation

To add custom callsign validation (e.g., local database):

Edit `src/packetclaude/auth/qrz_lookup.py`:

```python
def validate_callsign(self, callsign: str) -> bool:
    # Your custom validation here
    if callsign in my_local_database:
        return True
    # Fall back to QRZ
    return self.lookup(callsign) is not None
```

## Benefits

1. **Security**: Only licensed operators access the system
2. **Compliance**: Meets amateur radio regulations
3. **Accountability**: Know who's using the system
4. **Personalization**: Greet users by name
5. **Context**: Claude knows operator's location, license class
6. **Verification**: Ensures callsigns are valid and current

## Future Enhancements

Possible improvements:

1. **Local callsign database** - Reduce QRZ API calls
2. **Session persistence** - Remember authenticated users
3. **License class restrictions** - Require certain license levels
4. **Location-based features** - Use grid square for propagation info
5. **Callsign certificate exchange** - For secure authentication
6. **Multi-factor auth** - Beyond just callsign
7. **FCC ULS integration** - Alternative to QRZ.com

## See Also

- [QRZ.com XML API Documentation](https://www.qrz.com/XML/current_spec.html)
- [Telnet Login Detection](TELNET_LOGIN.md) - Automatic callsign from telnet
- [Session Management](../src/packetclaude/claude/session.py) - Session code
- [Rate Limiting](../src/packetclaude/auth/rate_limiter.py) - Per-callsign limits

---

**Important**: Keep your QRZ credentials secure! Don't commit `.env` file to version control.
