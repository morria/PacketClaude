#!/usr/bin/env python3
"""
Test POTA spots functionality
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.packetclaude.tools.pota_spots import POTASpotsTool


def test_pota_spots():
    """Test POTA spots tool"""
    print("Testing POTA spots tool...")

    # Create POTA tool
    tool = POTASpotsTool(enabled=True)

    # Test getting all spots from last 30 minutes
    print("\n1. Testing: Get all POTA spots from last 30 minutes")
    result = tool.get_spots(band=None, minutes=30)
    result_data = json.loads(result)

    if "error" in result_data:
        print(f"✗ Failed: {result_data['error']}")
        return False

    print(f"✓ Found {result_data['count']} total spots")
    if result_data['count'] > 0:
        print(f"   Sample spot: {result_data['spots'][0]['activator']} on {result_data['spots'][0]['frequency']} kHz")

    # Test getting 20m spots
    print("\n2. Testing: Get 20m spots from last 30 minutes")
    result = tool.get_spots(band="20m", minutes=30)
    result_data = json.loads(result)

    if "error" in result_data:
        print(f"✗ Failed: {result_data['error']}")
        return False

    print(f"✓ Found {result_data['count']} spots on 20m")

    # Display first few 20m spots
    if result_data['count'] > 0:
        print("\n   Recent 20m spots:")
        for idx, spot in enumerate(result_data['spots'][:5], 1):
            print(f"   {idx}. {spot['activator']} @ {spot['frequency']} kHz")
            print(f"      Park: {spot['park']} - {spot['park_name']}")
            print(f"      Mode: {spot['mode']}, Time: {spot['time']}")
            if spot.get('comments'):
                print(f"      Comments: {spot['comments']}")
            print()

    # Test tool definition
    print("3. Testing tool definition...")
    definition = tool.get_tool_definition()
    print(f"✓ Tool name: {definition['name']}")
    print(f"✓ Tool description: {definition['description'][:60]}...")

    # Test execute_tool
    print("\n4. Testing execute_tool method...")
    result = tool.execute_tool("pota_spots", {"band": "40m", "minutes": 30})
    result_data = json.loads(result)
    if "error" not in result_data:
        print(f"✓ execute_tool works, found {result_data['count']} spots on 40m")
    else:
        print(f"✗ execute_tool failed: {result_data['error']}")
        return False

    # Test band conversion
    print("\n5. Testing band conversion...")
    test_freqs = [
        (14250, "20m"),
        (7100, "40m"),
        (3700, "80m"),
        (21200, "15m"),
        (28500, "10m")
    ]

    for freq_khz, expected_band in test_freqs:
        band = tool._freq_to_band(freq_khz)
        if band == expected_band:
            print(f"✓ {freq_khz} kHz -> {band}")
        else:
            print(f"✗ {freq_khz} kHz -> {band} (expected {expected_band})")
            return False

    print("\n✓ All tests passed!")
    return True


if __name__ == '__main__':
    success = test_pota_spots()
    sys.exit(0 if success else 1)
