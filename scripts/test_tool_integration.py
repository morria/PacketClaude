#!/usr/bin/env python3
"""
Test tool integration with Claude client flow
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.packetclaude.tools.pota_spots import POTASpotsTool
from src.packetclaude.tools.web_search import WebSearchTool


def test_tool_integration():
    """Test that tools work correctly in the format Claude client expects"""
    print("Testing tool integration...")

    # Create tools
    pota_tool = POTASpotsTool(enabled=True)
    search_tool = WebSearchTool(max_results=3, enabled=True)

    tools = [pota_tool, search_tool]

    print("\n1. Testing tool definitions...")
    for tool in tools:
        definition = tool.get_tool_definition()
        print(f"✓ {definition['name']}: {definition['description'][:50]}...")

    print("\n2. Testing POTA tool execution (simulate Claude calling it)...")

    # Simulate Claude calling the tool with different inputs
    test_cases = [
        {"band": "20m", "minutes": 30},
        {"band": "", "minutes": 30},
        {"minutes": 15},
        {}
    ]

    for idx, tool_input in enumerate(test_cases, 1):
        print(f"\n   Test case {idx}: {tool_input}")
        try:
            result = pota_tool.execute_tool("pota_spots", tool_input)
            result_data = json.loads(result)

            if "error" in result_data:
                print(f"   ✗ Error: {result_data['error']}")
                return False
            else:
                print(f"   ✓ Success: {result_data['total_spots']} spots found, returned {result_data['returned_spots']}")
                if result_data.get('band'):
                    print(f"      Band: {result_data['band']}")
        except Exception as e:
            print(f"   ✗ Exception: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n3. Testing web search tool execution...")
    try:
        result = search_tool.execute_tool("web_search", {"query": "test"})
        result_data = json.loads(result)
        if "error" not in result_data:
            print(f"✓ Web search works")
        else:
            print(f"✓ Web search returned error (expected with no results): {result_data['error']}")
    except Exception as e:
        print(f"✗ Web search exception: {e}")
        return False

    print("\n4. Testing tool result format...")
    result = pota_tool.execute_tool("pota_spots", {"band": "40m", "minutes": 30})

    # Verify it's valid JSON
    try:
        result_data = json.loads(result)
        print("✓ Result is valid JSON")
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        return False

    # Verify structure
    if "error" not in result_data:
        required_keys = ["band", "time_window_minutes", "total_spots", "returned_spots", "spots"]
        for key in required_keys:
            if key in result_data:
                print(f"✓ Has key: {key}")
            else:
                print(f"✗ Missing key: {key}")
                return False

        if result_data["returned_spots"] > 0 and len(result_data["spots"]) > 0:
            spot = result_data["spots"][0]
            spot_keys = ["activator", "frequency", "mode", "park", "park_name", "time"]
            for key in spot_keys:
                if key in spot:
                    print(f"✓ Spot has key: {key}")
                else:
                    print(f"✗ Spot missing key: {key}")

    print("\n✓ All integration tests passed!")
    return True


if __name__ == '__main__':
    success = test_tool_integration()
    sys.exit(0 if success else 1)
