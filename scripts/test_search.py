#!/usr/bin/env python3
"""
Test web search functionality
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.packetclaude.tools.web_search import WebSearchTool


def test_search():
    """Test basic search functionality"""
    print("Testing web search tool...")

    # Create search tool
    tool = WebSearchTool(max_results=3, enabled=True)

    # Test search
    query = "latest news about AI"
    print(f"\nSearching for: {query}")

    result = tool.search(query)
    result_data = json.loads(result)

    if "error" in result_data:
        print(f"✗ Search failed: {result_data['error']}")
        return False

    print(f"✓ Found {len(result_data['results'])} results\n")

    # Display results
    for idx, item in enumerate(result_data['results'], 1):
        print(f"{idx}. {item['title']}")
        print(f"   {item['url']}")
        print(f"   {item['snippet'][:100]}...")
        print()

    # Test tool definition
    print("Testing tool definition...")
    definition = tool.get_tool_definition()
    print(f"✓ Tool name: {definition['name']}")
    print(f"✓ Tool description: {definition['description'][:50]}...")

    # Test execute_tool
    print("\nTesting execute_tool method...")
    result = tool.execute_tool("web_search", {"query": "Python programming"})
    result_data = json.loads(result)
    if "error" not in result_data:
        print(f"✓ execute_tool works, found {len(result_data['results'])} results")
    else:
        print(f"✗ execute_tool failed: {result_data['error']}")
        return False

    print("\n✓ All tests passed!")
    return True


if __name__ == '__main__':
    success = test_search()
    sys.exit(0 if success else 1)
