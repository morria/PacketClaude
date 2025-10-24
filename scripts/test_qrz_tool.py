#!/usr/bin/env python3
"""
Test script for QRZ tool integration with Claude
"""
import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from packetclaude.auth.qrz_lookup import QRZLookup
from packetclaude.tools.qrz_tool import QRZTool
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()

    api_key = os.getenv('QRZ_API_KEY', '')
    username = os.getenv('QRZ_USERNAME', '')
    password = os.getenv('QRZ_PASSWORD', '')

    print("=" * 70)
    print("QRZ Tool Integration Test")
    print("=" * 70)
    print()

    # Check credentials
    if not (api_key or (username and password)):
        print("✗ No QRZ credentials found in .env")
        print()
        print("Please add QRZ credentials to your .env file")
        return 1

    # Initialize QRZ lookup
    qrz_lookup = QRZLookup(
        api_key=api_key,
        username=username,
        password=password,
        enabled=True
    )

    # Initialize QRZ tool
    qrz_tool = QRZTool(
        qrz_lookup=qrz_lookup,
        enabled=True
    )

    print("Testing QRZ Tool for Claude\n")
    print("-" * 70)

    # Test 1: Get tool description
    print("\n1. Tool Description:")
    print("-" * 70)
    tool_desc = qrz_tool.get_tool_description()
    print(f"Tool Name: {tool_desc['name']}")
    print(f"Description: {tool_desc['description']}")
    print(f"Required Parameters: {tool_desc['input_schema']['required']}")

    # Test 2: Look up valid callsign
    print("\n2. Valid Callsign Lookup (W1AW):")
    print("-" * 70)
    result = qrz_tool.execute_tool("qrz_lookup", {"callsign": "W1AW"})
    result_data = json.loads(result)
    if result_data.get('found'):
        print(f"✓ Found: {result_data['callsign']}")
        if 'operator' in result_data:
            op = result_data['operator']
            if 'name' in op:
                print(f"  Name: {op['name']}")
            if 'country' in op:
                print(f"  Country: {op['country']}")
            if 'license_class' in op:
                print(f"  License Class: {op['license_class']}")
            if 'grid_square' in op:
                print(f"  Grid Square: {op['grid_square']}")
    else:
        print(f"✗ Not found: {result_data.get('message', 'Unknown error')}")

    # Test 3: Look up another valid callsign
    print("\n3. Another Valid Callsign (K1TTT):")
    print("-" * 70)
    result = qrz_tool.execute_tool("qrz_lookup", {"callsign": "K1TTT"})
    result_data = json.loads(result)
    if result_data.get('found'):
        print(f"✓ Found: {result_data['callsign']}")
        if 'operator' in result_data:
            op = result_data['operator']
            if 'name' in op:
                print(f"  Name: {op['name']}")
            if 'address' in op:
                print(f"  Address: {op['address']}")
    else:
        print(f"✗ Not found: {result_data.get('message', 'Unknown error')}")

    # Test 4: Look up invalid callsign
    print("\n4. Invalid Callsign (INVALID123):")
    print("-" * 70)
    result = qrz_tool.execute_tool("qrz_lookup", {"callsign": "INVALID123"})
    result_data = json.loads(result)
    if not result_data.get('found'):
        print(f"✓ Correctly reported as not found")
        print(f"  Message: {result_data.get('message', 'No message')}")
    else:
        print(f"✗ Unexpectedly found invalid callsign")

    # Test 5: Test missing parameter
    print("\n5. Missing Parameter Test:")
    print("-" * 70)
    result = qrz_tool.execute_tool("qrz_lookup", {})
    result_data = json.loads(result)
    if 'error' in result_data:
        print(f"✓ Correctly reported error for missing parameter")
        print(f"  Error: {result_data.get('message', 'No message')}")
    else:
        print(f"✗ Should have reported error for missing parameter")

    # Test 6: Display full JSON output
    print("\n6. Full JSON Output Example (W1AW):")
    print("-" * 70)
    result = qrz_tool.lookup_callsign("W1AW")
    print(result)

    print()
    print("=" * 70)
    print("Test Complete!")
    print("=" * 70)
    print()
    print("The QRZ tool is ready to use with Claude.")
    print("Users can now ask Claude things like:")
    print("  - 'Look up callsign W1AW'")
    print("  - 'What can you tell me about K1TTT?'")
    print("  - 'Find information on callsign N0CALL'")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
