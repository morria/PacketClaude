#!/usr/bin/env python3
"""
Test KISS connection to Direwolf
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from packetclaude.ax25.kiss import KISSClient
from packetclaude.ax25.protocol import AX25Frame


def main():
    print("Testing KISS connection to Direwolf...")
    print("Make sure Direwolf is running with KISS enabled on port 8001")
    print()

    # Create KISS client
    kiss = KISSClient(host='localhost', port=8001, timeout=10)

    # Connect
    print("Connecting to Direwolf...")
    if not kiss.connect():
        print("Failed to connect!")
        return 1

    print("Connected successfully!")
    print()

    # Try to receive a frame
    print("Waiting for incoming frames (10 second timeout)...")
    print("You can test by sending a packet from another station")
    print()

    frame_data = kiss.receive_frame(timeout=10.0)

    if frame_data:
        print(f"Received frame ({len(frame_data)} bytes)")
        try:
            frame = AX25Frame.decode(frame_data)
            print(f"  From: {frame.source}")
            print(f"  To: {frame.destination}")
            print(f"  Type: {frame.get_frame_type().name}")
            if frame.info:
                info_text = frame.info.decode('utf-8', errors='ignore')
                print(f"  Info: {info_text}")
        except Exception as e:
            print(f"  Error decoding frame: {e}")
    else:
        print("No frames received (timeout)")

    print()
    print("Test complete. Disconnecting...")
    kiss.disconnect()

    return 0


if __name__ == '__main__':
    sys.exit(main())
