#!/usr/bin/env python3
"""
Test BBS Session Tool
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_tool_definition():
    """Test that tool definition is valid"""
    print("\n=== Testing Tool Definition ===")

    from packetclaude.tools.bbs_session import BBSSessionTool

    # Create a mock app with minimal required attributes
    class MockApp:
        def __init__(self):
            from packetclaude.claude.session import SessionManager
            self.session_manager = SessionManager()
            self.connection_handler = None
            self.telnet_server = None

            class MockConfig:
                search_enabled = True
                pota_enabled = True

            self.config = MockConfig()

    mock_app = MockApp()
    tool = BBSSessionTool(mock_app)

    definition = tool.get_tool_definition()

    print(f"Tool name: {definition['name']}")
    print(f"Description: {definition['description'][:50]}...")
    print(f"Actions available: {definition['input_schema']['properties']['action']['enum']}")

    assert definition['name'] == 'bbs_session', "Tool name should be bbs_session"
    assert 'action' in definition['input_schema']['properties'], "Should have action property"
    assert len(definition['input_schema']['properties']['action']['enum']) == 8, "Should have 8 actions"

    print("✓ Tool definition is valid")
    return True


def test_get_help():
    """Test get_help action"""
    print("\n=== Testing get_help Action ===")

    from packetclaude.tools.bbs_session import BBSSessionTool
    from packetclaude.claude.session import SessionManager

    class MockApp:
        def __init__(self):
            self.session_manager = SessionManager()
            self.connection_handler = None
            self.telnet_server = None
            class MockConfig:
                search_enabled = True
                pota_enabled = True
            self.config = MockConfig()

    mock_app = MockApp()
    tool = BBSSessionTool(mock_app)

    result = tool.execute_tool("bbs_session", {"action": "get_help"})
    result_data = json.loads(result)

    print(f"Success: {result_data['success']}")
    print(f"Help sections: {list(result_data['help'].keys())}")

    assert result_data['success'], "get_help should succeed"
    assert 'bbs_commands' in result_data['help'], "Should have bbs_commands section"
    assert 'claude_interaction' in result_data['help'], "Should have claude_interaction section"

    print("✓ get_help works correctly")
    return True


def test_get_status():
    """Test get_status action"""
    print("\n=== Testing get_status Action ===")

    from packetclaude.tools.bbs_session import BBSSessionTool
    from packetclaude.claude.session import SessionManager

    class MockApp:
        def __init__(self):
            self.session_manager = SessionManager()
            self.connection_handler = None
            self.telnet_server = None
            class MockConfig:
                search_enabled = True
                pota_enabled = True
            self.config = MockConfig()

    mock_app = MockApp()
    tool = BBSSessionTool(mock_app)

    result = tool.execute_tool("bbs_session", {"action": "get_status"})
    result_data = json.loads(result)

    print(f"Success: {result_data['success']}")
    print(f"System name: {result_data['system']['name']}")
    print(f"Active sessions: {result_data['sessions']['active_sessions']}")
    print(f"Tools available: search={result_data['tools']['web_search']}, pota={result_data['tools']['pota_spots']}")

    assert result_data['success'], "get_status should succeed"
    assert result_data['system']['name'] == 'PacketClaude', "System name should be PacketClaude"

    print("✓ get_status works correctly")
    return True


def test_get_session_info():
    """Test get_session_info action"""
    print("\n=== Testing get_session_info Action ===")

    from packetclaude.tools.bbs_session import BBSSessionTool
    from packetclaude.claude.session import SessionManager

    class MockApp:
        def __init__(self):
            self.session_manager = SessionManager()
            self.connection_handler = None
            self.telnet_server = None
            class MockConfig:
                search_enabled = True
                pota_enabled = True
            self.config = MockConfig()

    mock_app = MockApp()
    tool = BBSSessionTool(mock_app)

    # Create a session
    mock_app.session_manager.add_user_message("K0ASM", "test message")

    result = tool.execute_tool("bbs_session", {"action": "get_session_info", "connection_id": "K0ASM"})
    result_data = json.loads(result)

    print(f"Success: {result_data['success']}")
    print(f"Callsign: {result_data['session']['callsign']}")
    print(f"Messages: {result_data['session']['messages']}")
    print(f"Queries: {result_data['session']['queries']}")

    assert result_data['success'], "get_session_info should succeed"
    assert result_data['session']['callsign'] == 'K0ASM', "Callsign should be K0ASM"
    assert result_data['session']['messages'] == 1, "Should have 1 message"

    print("✓ get_session_info works correctly")
    return True


def test_list_users():
    """Test list_users action"""
    print("\n=== Testing list_users Action ===")

    from packetclaude.tools.bbs_session import BBSSessionTool
    from packetclaude.claude.session import SessionManager

    class MockApp:
        def __init__(self):
            self.session_manager = SessionManager()
            self.connection_handler = None
            self.telnet_server = None
            class MockConfig:
                search_enabled = True
                pota_enabled = True
            self.config = MockConfig()

    mock_app = MockApp()
    tool = BBSSessionTool(mock_app)

    result = tool.execute_tool("bbs_session", {"action": "list_users"})
    result_data = json.loads(result)

    print(f"Success: {result_data['success']}")
    print(f"Total users: {result_data['total_users']}")
    print(f"Users: {result_data['users']}")

    assert result_data['success'], "list_users should succeed"
    assert result_data['total_users'] == 0, "Should have 0 users (no connections)"

    print("✓ list_users works correctly")
    return True


def test_clear_history():
    """Test clear_history action"""
    print("\n=== Testing clear_history Action ===")

    from packetclaude.tools.bbs_session import BBSSessionTool
    from packetclaude.claude.session import SessionManager

    class MockApp:
        def __init__(self):
            self.session_manager = SessionManager()
            self.connection_handler = None
            self.telnet_server = None
            class MockConfig:
                search_enabled = True
                pota_enabled = True
            self.config = MockConfig()

    mock_app = MockApp()
    tool = BBSSessionTool(mock_app)

    # Add some messages
    mock_app.session_manager.add_user_message("W1ABC", "test 1")
    mock_app.session_manager.add_user_message("W1ABC", "test 2")

    # Verify messages exist
    history = mock_app.session_manager.get_history("W1ABC")
    assert len(history) == 2, "Should have 2 messages before clear"

    # Clear history
    result = tool.execute_tool("bbs_session", {"action": "clear_history", "connection_id": "W1ABC"})
    result_data = json.loads(result)

    print(f"Success: {result_data['success']}")
    print(f"Message: {result_data['message']}")

    # Verify messages cleared
    history = mock_app.session_manager.get_history("W1ABC")
    assert len(history) == 0, "Should have 0 messages after clear"

    assert result_data['success'], "clear_history should succeed"

    print("✓ clear_history works correctly")
    return True


if __name__ == '__main__':
    print("BBS Session Tool Unit Tests")
    print("=" * 50)

    try:
        test_tool_definition()
        test_get_help()
        test_get_status()
        test_get_session_info()
        test_list_users()
        test_clear_history()

        print("\n" + "=" * 50)
        print("✓ All unit tests passed!")
        print("\nNext steps:")
        print("  1. Start PacketClaude: ./packetclaude.py --telnet-only")
        print("  2. Connect: telnet localhost 8023")
        print("  3. Try BBS commands through Claude:")
        print("     - 'show me my session info'")
        print("     - 'who else is connected?'")
        print("     - 'what's the system status?'")
        print("     - 'clear my conversation history'")
        sys.exit(0)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
