#!/usr/bin/env python3
"""
Check that PacketClaude starts up correctly with tools enabled
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.packetclaude.config import Config
from src.packetclaude.tools.pota_spots import POTASpotsTool
from src.packetclaude.tools.web_search import WebSearchTool


def check_startup():
    """Verify configuration and tools load correctly"""
    print("Checking PacketClaude startup configuration...\n")

    # Load config
    try:
        config = Config()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False

    # Check POTA enabled
    print(f"  - POTA enabled: {config.pota_enabled}")
    print(f"  - Search enabled: {config.search_enabled}")
    print(f"  - Telnet enabled: {config.telnet_enabled}")

    # Initialize tools (like main.py does)
    print("\nInitializing tools...")
    tools = []

    if config.search_enabled:
        try:
            search_tool = WebSearchTool(
                max_results=config.search_max_results,
                enabled=True
            )
            tools.append(search_tool)
            print("✓ Web search tool initialized")
        except Exception as e:
            print(f"✗ Failed to initialize web search: {e}")
            return False

    if config.pota_enabled:
        try:
            pota_tool = POTASpotsTool(enabled=True)
            tools.append(pota_tool)
            print("✓ POTA spots tool initialized")
        except Exception as e:
            print(f"✗ Failed to initialize POTA tool: {e}")
            return False

    print(f"\nTotal tools loaded: {len(tools)}")

    # Get tool definitions
    print("\nTool definitions:")
    for tool in tools:
        definition = tool.get_tool_definition()
        print(f"  - {definition['name']}: {definition['description'][:60]}...")

    # Test a POTA call
    if config.pota_enabled:
        print("\nTesting POTA tool call...")
        for tool in tools:
            if hasattr(tool, 'execute_tool'):
                try:
                    result = tool.execute_tool("pota_spots", {"band": "20m", "minutes": 30})
                    import json
                    result_data = json.loads(result)
                    if "error" not in result_data:
                        print(f"✓ POTA tool works! Found {result_data['count']} spots on 20m")
                        break
                except Exception as e:
                    print(f"✗ POTA tool error: {e}")
                    import traceback
                    traceback.print_exc()

    print("\n✓ Startup check complete!")
    return True


if __name__ == '__main__':
    success = check_startup()
    sys.exit(0 if success else 1)
