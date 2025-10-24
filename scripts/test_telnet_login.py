#!/usr/bin/env python3
"""
Test telnet login name detection
"""
import sys
import socket
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Telnet protocol constants
IAC = b'\xff'
WILL = b'\xfb'
WONT = b'\xfc'
DO = b'\xfd'
DONT = b'\xfe'
SB = b'\xfa'
SE = b'\xf0'
TELOPT_NEW_ENVIRON = b'\x27'


def send_environ_with_user(sock, username):
    """Send NEW-ENVIRON subnegotiation with USER variable"""
    # Format: IAC SB NEW-ENVIRON IS VAR "USER" VALUE "username" IAC SE
    # IS = 0, VAR = 0, VALUE = 1
    IS = b'\x00'
    VAR = b'\x00'
    VALUE = b'\x01'

    user_bytes = username.encode('ascii')
    env_data = IS + VAR + b'USER' + VALUE + user_bytes

    response = IAC + SB + TELOPT_NEW_ENVIRON + env_data + IAC + SE
    sock.sendall(response)
    print(f"  Sent USER={username} via NEW-ENVIRON")


def test_telnet_login(host='localhost', port=8023, username='K0ASM'):
    """Test telnet connection with login name"""
    print(f"\n=== Testing Telnet Login Detection ===")
    print(f"Host: {host}:{port}")
    print(f"Username: {username}")

    try:
        # Connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        print("✓ Connected")

        # Wait for server to send DO NEW-ENVIRON
        time.sleep(0.1)

        # Read any initial data from server
        try:
            sock.settimeout(0.5)
            data = sock.recv(1024)
            if IAC in data and DO in data and TELOPT_NEW_ENVIRON in data:
                print("✓ Server requested NEW-ENVIRON")
            else:
                print("  Server sent:", repr(data))
        except socket.timeout:
            pass

        # Send environment with USER variable
        send_environ_with_user(sock, username)

        # Wait for processing
        time.sleep(0.2)

        # Send a test message
        sock.sendall(b"help\r\n")
        print("✓ Sent test command")

        # Read response
        sock.settimeout(2.0)
        response = sock.recv(4096)
        print(f"✓ Received response ({len(response)} bytes)")

        # Clean up
        sock.sendall(b"quit\r\n")
        time.sleep(0.1)
        sock.close()

        print("\n=== Test Complete ===")
        print("Check logs/ for:")
        print(f"  - 'Detected telnet login for ... : {username}'")
        print(f"  - 'Connection ... identified as {username.upper()}'")
        print(f"  - Rate limiter using '{username.upper()}' instead of IP:port")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_without_login(host='localhost', port=8023):
    """Test telnet connection without login name (fallback to IP:port)"""
    print(f"\n=== Testing Fallback (No Login) ===")
    print(f"Host: {host}:{port}")

    try:
        # Connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        print("✓ Connected")

        # Don't send environment - just send a command
        time.sleep(0.2)
        sock.sendall(b"help\r\n")
        print("✓ Sent test command (no login)")

        # Read response
        sock.settimeout(2.0)
        response = sock.recv(4096)
        print(f"✓ Received response ({len(response)} bytes)")

        # Clean up
        sock.sendall(b"quit\r\n")
        time.sleep(0.1)
        sock.close()

        print("\n=== Test Complete ===")
        print("Check logs for connection using IP:port format")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == '__main__':
    print("Telnet Login Name Detection Test")
    print("=" * 50)
    print("\nMake sure PacketClaude is running in telnet mode:")
    print("  ./packetclaude.py --telnet-only")
    print()

    # Test with login name
    success1 = test_telnet_login(username='K0ASM')

    # Test without login name (fallback)
    time.sleep(1)
    success2 = test_without_login()

    print("\n" + "=" * 50)
    if success1 and success2:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
