#!/usr/bin/env python3
"""
Test what telnet actually sends when using -l flag
"""
import socket
import threading
import time

def telnet_server():
    """Simple server to see what telnet sends"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', 8888))
    server.listen(1)

    print("Test server listening on localhost:8888")
    print("In another terminal, run: telnet -l w2asm localhost 8888")
    print()

    conn, addr = server.accept()
    print(f"Connection from {addr}")

    # Send IAC DO NEW-ENVIRON
    IAC = b'\xff'
    DO = b'\xfd'
    TELOPT_NEW_ENVIRON = b'\x27'

    print(f"Sending: IAC DO NEW-ENVIRON = {repr(IAC + DO + TELOPT_NEW_ENVIRON)}")
    conn.sendall(IAC + DO + TELOPT_NEW_ENVIRON)

    # Receive data
    print("\nWaiting for client response...")
    time.sleep(1)

    data = conn.recv(4096)
    print(f"\nReceived {len(data)} bytes:")
    print(f"Raw: {repr(data)}")
    print(f"Hex: {data.hex()}")

    # Parse for IAC sequences
    if b'\xff' in data:
        print("\n✓ Found IAC sequences in response")

        # Look for WILL/WONT NEW-ENVIRON
        WILL = b'\xfb'
        WONT = b'\xfc'
        if WILL + TELOPT_NEW_ENVIRON in data:
            print("✓ Client sent WILL NEW-ENVIRON (supports it!)")
        elif WONT + TELOPT_NEW_ENVIRON in data:
            print("✗ Client sent WONT NEW-ENVIRON (doesn't support it)")

        # Look for subnegotiation
        SB = b'\xfa'
        SE = b'\xf0'
        if SB in data and SE in data:
            print("✓ Found subnegotiation (SB...SE)")
            sb_start = data.index(SB)
            se_start = data.index(SE, sb_start)
            subneg_data = data[sb_start:se_start+1]
            print(f"  Subnegotiation: {repr(subneg_data)}")
    else:
        print("✗ No IAC sequences found - client not sending telnet protocol")

    conn.close()
    server.close()

if __name__ == '__main__':
    print("Telnet Protocol Test")
    print("=" * 60)
    print()
    telnet_server()
