#!/usr/bin/env python3
"""
Test script for QRZ API key authentication
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from packetclaude.auth.qrz_lookup import QRZLookup
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()

    api_key = os.getenv('QRZ_API_KEY', '')
    username = os.getenv('QRZ_USERNAME', '')
    password = os.getenv('QRZ_PASSWORD', '')

    print("=" * 60)
    print("QRZ API Authentication Test")
    print("=" * 60)
    print()

    # Check what credentials we have
    if api_key:
        print(f"✓ Found QRZ_API_KEY: {api_key[:8]}...")
        auth_method = "API Key"
    elif username and password:
        print(f"✓ Found QRZ_USERNAME: {username}")
        print(f"✓ Found QRZ_PASSWORD: {'*' * len(password)}")
        auth_method = "Username/Password"
    else:
        print("✗ No QRZ credentials found in .env")
        print()
        print("Please add one of the following to your .env file:")
        print()
        print("Option 1 (Recommended):")
        print("  QRZ_API_KEY=your_api_key")
        print()
        print("Option 2 (Free):")
        print("  QRZ_USERNAME=your_username")
        print("  QRZ_PASSWORD=your_password")
        return 1

    print(f"Authentication method: {auth_method}")
    print()

    # Initialize QRZ lookup
    qrz = QRZLookup(
        api_key=api_key,
        username=username,
        password=password,
        enabled=True
    )

    # Test callsigns
    test_callsigns = ['W1AW', 'K1TTT', 'INVALID123']

    print("Testing callsign lookups:")
    print("-" * 60)

    for callsign in test_callsigns:
        print(f"\nLooking up: {callsign}")
        result = qrz.lookup(callsign)

        if result:
            print(f"  ✓ Found!")
            print(f"    Name: {result.get('fullname', 'Unknown')}")
            print(f"    Location: {result.get('state', 'Unknown')}, {result.get('country', 'Unknown')}")
            print(f"    License: {result.get('class', 'Unknown')}")
            if result.get('grid'):
                print(f"    Grid: {result.get('grid')}")
        else:
            print(f"  ✗ Not found or error")

    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
