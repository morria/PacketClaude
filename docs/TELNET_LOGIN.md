# Telnet Login Name Detection

PacketClaude can automatically detect your callsign when you connect via telnet by reading environment variables sent by your telnet client.

## How It Works

When you connect via telnet, PacketClaude:

1. **Requests environment variables** from your telnet client using the NEW-ENVIRON option (RFC 1572)
2. **Looks for login information** in the `USER` or `LOGNAME` environment variables
3. **Uses your login name as your callsign** for rate limiting and identification
4. **Falls back to IP:port** if no login name is detected

## Benefits

- **Persistent identity**: Your callsign stays the same across connections
- **Proper rate limiting**: Rate limits apply to your callsign, not your IP
- **Better logs**: Logs show your callsign instead of IP:port
- **Ham radio convention**: Uses callsigns just like packet radio connections

## Telnet Client Support

### Modern Telnet Clients

Most modern telnet clients support sending environment variables:

**Linux/macOS (telnet)**
```bash
telnet localhost 8023
```
The standard telnet client automatically sends your Unix username via USER variable.

**PuTTY (Windows/Linux)**
- Connection → Telnet → Environment
- Add: `USER` = `K0ASM` (your callsign)

**SecureCRT**
- Session Options → Connection → Telnet → Environment
- Add: `USER` = `K0ASM`

**netcat (nc)**
```bash
nc localhost 8023
```
⚠️ netcat does NOT send environment variables - will fallback to IP:port

### Testing Your Client

Connect and check the logs:

```bash
# In terminal 1 - start PacketClaude
./packetclaude.py --telnet-only

# In terminal 2 - connect
telnet localhost 8023

# In terminal 3 - check logs
tail -f logs/packetclaude_*.log | grep "identified as"
```

You should see:
```
Connection 127.0.0.1:54321 identified as K0ASM
```

If you see IP:port format in logs, your client isn't sending environment variables.

## Manual Callsign Configuration

If your telnet client doesn't support environment variables, you can:

### Option 1: Set Unix Username

Set your Unix username to your callsign:

```bash
# Temporarily (Linux/macOS)
su - k0asm
telnet localhost 8023

# Or set USER environment variable
USER=K0ASM telnet localhost 8023
```

### Option 2: Use Telnet with -l Flag

Some telnet clients support the `-l` flag:

```bash
telnet -l K0ASM localhost 8023
```

This sends K0ASM as the USER variable.

### Option 3: Accept IP:port Format

PacketClaude will work fine with IP:port format - it's just not as ham-radio-friendly.

## Protocol Details

PacketClaude implements:

- **RFC 854**: Telnet Protocol Specification
- **RFC 1572**: Telnet Environment Option

### Environment Variable Format

When your client connects, PacketClaude sends:
```
IAC DO NEW-ENVIRON
```

Compliant clients respond with:
```
IAC SB NEW-ENVIRON IS VAR "USER" VALUE "K0ASM" IAC SE
```

PacketClaude extracts the value and uses it as your callsign.

## Verification

### Check Your Callsign

After connecting via telnet:

```
status
```

The response will show your connection info with your callsign.

### Check Rate Limiting

Rate limits are applied per-callsign:

```bash
# In logs
grep "Rate limit" logs/packetclaude_*.log | tail -10
```

You'll see your callsign in rate limit messages instead of IP:port.

### Test Scripts

Run the included test scripts:

```bash
# Unit tests (no server required)
python scripts/test_telnet_parsing.py

# Integration test (requires running server)
# Terminal 1:
./packetclaude.py --telnet-only

# Terminal 2:
python scripts/test_telnet_login.py
```

## Troubleshooting

### My client sends environment variables but they're not detected

Check logs for:
```bash
grep "Detected telnet login" logs/packetclaude_*.log
```

If you see nothing, your client may not be sending USER or LOGNAME.

### I see "identified as 127.0.0.1:12345"

Your telnet client isn't sending environment variables. This is OK - PacketClaude will still work, but will use IP:port instead of your callsign.

### Can I send a custom variable?

Currently only `USER` and `LOGNAME` are recognized. To add more:

1. Edit `src/packetclaude/telnet/server.py`
2. Find `_parse_environ()` method
3. Add your variable name to the check:
```python
if var_name.upper() in ('USER', 'LOGNAME', 'CALLSIGN') and var_value:
```

## Security Considerations

- **Trust**: PacketClaude trusts the USER/LOGNAME sent by the client
- **No authentication**: This is NOT authentication - clients can send any value
- **Ham radio context**: This assumes good faith, like traditional packet radio
- **Rate limiting**: Prevents abuse even if someone spoofs a callsign

For secure authentication, you'd need to add:
- Password verification
- Certificate-based authentication
- Token-based authentication

These are beyond the scope of packet radio emulation.

## Examples

### Standard Telnet (Linux/macOS)

```bash
# Your Unix user is 'john'
$ whoami
john

$ telnet localhost 8023
# PacketClaude sees you as: JOHN
```

### Telnet with Custom User

```bash
$ USER=K0ASM telnet localhost 8023
# PacketClaude sees you as: K0ASM
```

### PuTTY Configuration

1. Create new session
2. Host: localhost, Port: 8023
3. Connection type: Telnet
4. Connection → Telnet → Environment
5. Add variable: `USER` = `K0ASM`
6. Save session as "PacketClaude"
7. Connect

### Raw Telnet Protocol

You can send environment manually:

```python
import socket

sock = socket.socket()
sock.connect(('localhost', 8023))

# Wait for DO NEW-ENVIRON
data = sock.recv(1024)

# Send: IAC SB NEW-ENVIRON IS VAR "USER" VALUE "K0ASM" IAC SE
IAC, SB, SE = b'\xff', b'\xfa', b'\xf0'
NEWENV = b'\x27'
IS, VAR, VALUE = b'\x00', b'\x00', b'\x01'

env = IAC + SB + NEWENV + IS + VAR + b'USER' + VALUE + b'K0ASM' + IAC + SE
sock.sendall(env)

# Now PacketClaude knows you as K0ASM
sock.sendall(b'help\r\n')
response = sock.recv(4096)
print(response)
```

## See Also

- [Running Modes](RUNNING_MODES.md) - How to start PacketClaude in telnet-only mode
- [Quick Start](../QUICK_START.md) - Getting started with telnet connections
- RFC 854: Telnet Protocol Specification
- RFC 1572: Telnet Environment Option
