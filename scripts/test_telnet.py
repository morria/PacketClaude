#!/usr/bin/env python3
"""
Test telnet server functionality
"""
import socket
import time
import sys


def test_telnet_connection(host='localhost', port=8023):
    """Test basic telnet connection"""
    print(f"Testing telnet connection to {host}:{port}...")

    try:
        # Connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        print("✓ Connected successfully")

        # Receive welcome message
        time.sleep(0.5)
        data = sock.recv(4096)
        print(f"\nReceived welcome message:")
        print(data.decode('utf-8', errors='ignore'))

        # Send a test message
        test_message = "Hello from test script\n"
        print(f"\nSending: {test_message.strip()}")
        sock.sendall(test_message.encode('utf-8'))

        # Receive response (may take a moment)
        print("Waiting for response...")
        time.sleep(2.0)
        data = sock.recv(4096)
        print(f"\nReceived response:")
        print(data.decode('utf-8', errors='ignore'))

        # Send quit
        print("\nSending: bye")
        sock.sendall(b"bye\n")
        time.sleep(0.5)

        # Close
        sock.close()
        print("\n✓ Test completed successfully")
        return True

    except ConnectionRefusedError:
        print(f"✗ Connection refused - is PacketClaude running with telnet enabled?")
        return False
    except socket.timeout:
        print(f"✗ Connection timeout")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8023

    success = test_telnet_connection(host, port)
    sys.exit(0 if success else 1)
