#!/usr/bin/env python3
"""Test QRZ lookup"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.packetclaude.auth.qrz_lookup import QRZLookup
from src.packetclaude.config import Config
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    if len(sys.argv) < 2:
        print("Usage: test_qrz.py <callsign>")
        sys.exit(1)

    callsign = sys.argv[1]

    # Load config
    config = Config()

    # Get QRZ credentials
    username = os.getenv('QRZ_USERNAME')
    password = os.getenv('QRZ_PASSWORD')
    api_key = os.getenv('QRZ_API_KEY')

    if not username or not password:
        print("Error: QRZ_USERNAME and QRZ_PASSWORD environment variables required")
        sys.exit(1)

    print(f"Testing QRZ lookup for: {callsign}")
    print(f"Username: {username}")
    print(f"API Key: {'***' if api_key else 'None'}")
    print()

    # Create QRZ lookup
    qrz = QRZLookup(username, password, api_key)

    # Test lookup
    result = qrz.lookup(callsign)

    if result:
        print("SUCCESS! QRZ data found:")
        print(f"  Callsign: {result.get('callsign')}")
        print(f"  Name: {result.get('fname')} {result.get('name')}")
        print(f"  Location: {result.get('addr2')}")
        print(f"  Grid: {result.get('grid')}")
        print(f"  Class: {result.get('class')}")
        print()
        print("Full result:")
        for key, value in sorted(result.items()):
            print(f"  {key}: {value}")
    else:
        print(f"FAILED: No data found for {callsign}")
        sys.exit(1)

if __name__ == '__main__':
    main()
