#!/usr/bin/env python3
"""
Test telnet protocol parsing logic (unit test)
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from packetclaude.telnet.server import TelnetServer, TelnetConnection, IAC, SB, SE, TELOPT_NEW_ENVIRON
import socket


def create_mock_connection():
    """Create a mock connection for testing"""
    # Create a mock socket (not actually connected)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn = TelnetConnection(sock, ("127.0.0.1", 12345))
    return conn


def test_environ_parsing():
    """Test parsing of NEW-ENVIRON telnet option"""
    print("\n=== Testing Environment Variable Parsing ===")

    server = TelnetServer()
    conn = create_mock_connection()

    # Format: VAR "USER" VALUE "K0ASM"
    # VAR = 0, VALUE = 1
    VAR = 0
    VALUE = 1
    env_data = bytes([0, VAR]) + b'USER' + bytes([VALUE]) + b'K0ASM'

    print(f"Initial state:")
    print(f"  Connection ID: {conn._remote_address}")
    print(f"  Callsign: {conn.callsign}")
    print(f"  remote_address property: {conn.remote_address}")

    # Parse the environment data
    server._parse_environ(conn, env_data)

    print(f"\nAfter parsing USER=K0ASM:")
    print(f"  Callsign: {conn.callsign}")
    print(f"  remote_address property: {conn.remote_address}")

    # Verify
    assert conn.callsign == "K0ASM", f"Expected 'K0ASM', got '{conn.callsign}'"
    assert conn.remote_address == "K0ASM", f"Expected remote_address='K0ASM', got '{conn.remote_address}'"
    print("✓ Callsign correctly detected and set")

    return True


def test_environ_parsing_logname():
    """Test parsing with LOGNAME variable"""
    print("\n=== Testing LOGNAME Variable ===")

    server = TelnetServer()
    conn = create_mock_connection()

    # Format: VAR "LOGNAME" VALUE "w1abc"
    VAR = 0
    VALUE = 1
    env_data = bytes([0, VAR]) + b'LOGNAME' + bytes([VALUE]) + b'w1abc'

    print(f"Initial callsign: {conn.callsign}")
    server._parse_environ(conn, env_data)

    print(f"After parsing LOGNAME=w1abc:")
    print(f"  Callsign: {conn.callsign}")
    print(f"  remote_address: {conn.remote_address}")

    assert conn.callsign == "W1ABC", f"Expected 'W1ABC', got '{conn.callsign}'"
    print("✓ LOGNAME correctly detected (uppercase conversion)")

    return True


def test_fallback_without_login():
    """Test fallback to IP:port when no login provided"""
    print("\n=== Testing Fallback (No Login) ===")

    conn = create_mock_connection()

    print(f"Without login:")
    print(f"  Callsign: {conn.callsign}")
    print(f"  remote_address: {conn.remote_address}")

    assert conn.callsign is None, "Callsign should be None"
    assert conn.remote_address == "127.0.0.1:12345", f"Expected IP:port, got '{conn.remote_address}'"
    print("✓ Correctly falls back to IP:port format")

    return True


def test_telnet_data_parsing():
    """Test parsing telnet protocol sequences from data stream"""
    print("\n=== Testing Telnet Data Parsing ===")

    server = TelnetServer()
    conn = create_mock_connection()

    # Create telnet data with IAC SB NEW-ENVIRON ... IAC SE
    # Format: IAC SB NEW-ENVIRON IS VAR "USER" VALUE "K0ASM" IAC SE
    IS = b'\x00'
    VAR = b'\x00'
    VALUE = b'\x01'

    env_payload = IS + VAR + b'USER' + VALUE + b'K0ASM'
    telnet_data = IAC + SB + TELOPT_NEW_ENVIRON + env_payload + IAC + SE

    # Add some text before and after
    test_data = b"Hello " + telnet_data + b"World"

    print(f"Test data: {repr(test_data[:20])}...{repr(test_data[-10:])}")
    print(f"Data length: {len(test_data)} bytes")

    # Parse the data
    result = server._parse_telnet_data(conn, test_data)

    print(f"\nResult:")
    print(f"  Parsed data: {repr(result)}")
    print(f"  Callsign detected: {conn.callsign}")
    print(f"  remote_address: {conn.remote_address}")

    assert result == b"Hello World", f"Expected 'Hello World', got '{result}'"
    assert conn.callsign == "K0ASM", f"Expected callsign 'K0ASM', got '{conn.callsign}'"
    print("✓ Telnet protocol sequences correctly parsed and removed")

    return True


if __name__ == '__main__':
    print("Telnet Protocol Parsing Unit Tests")
    print("=" * 50)

    try:
        test_fallback_without_login()
        test_environ_parsing()
        test_environ_parsing_logname()
        test_telnet_data_parsing()

        print("\n" + "=" * 50)
        print("✓ All unit tests passed!")
        print("\nNext steps:")
        print("  1. Start PacketClaude: ./packetclaude.py --telnet-only")
        print("  2. Run integration test: python scripts/test_telnet_login.py")
        print("  3. Or connect manually: telnet localhost 8023")
        sys.exit(0)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
