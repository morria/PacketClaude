"""
BBS Session Tool for Claude
Allows Claude to interact with the BBS system, get session info, and help users
"""
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class BBSSessionTool:
    """
    Tool for Claude to interact with BBS session information
    """

    def __init__(self, packetclaude_app):
        """
        Initialize BBS session tool

        Args:
            packetclaude_app: Reference to main PacketClaude application
        """
        self.app = packetclaude_app
        self.enabled = True

    def get_tool_definition(self) -> Dict:
        """
        Get tool definition for Claude API

        Returns:
            Tool definition dictionary
        """
        return {
            "name": "bbs_session",
            "description": """
Interact with the PacketClaude BBS system. Use this tool to:
- Get information about the current user's session
- Get/set user callsigns for telnet connections
- Show list of connected users
- Display help information
- Get system status and statistics
- Clear conversation history
- Exit/disconnect users

This tool provides complete BBS system control and information.
""".strip(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_session_info",
                            "get_callsign",
                            "set_callsign",
                            "list_users",
                            "get_help",
                            "get_status",
                            "clear_history",
                            "disconnect"
                        ],
                        "description": "The action to perform"
                    },
                    "connection_id": {
                        "type": "string",
                        "description": "Connection identifier (callsign or IP:port) - required for most actions"
                    },
                    "callsign": {
                        "type": "string",
                        "description": "New callsign to set (only for set_callsign action)"
                    }
                },
                "required": ["action"]
            }
        }

    def execute(self, action: str, connection_id: Optional[str] = None,
                callsign: Optional[str] = None) -> str:
        """
        Execute BBS session action

        Args:
            action: Action to perform
            connection_id: Connection identifier (callsign or IP:port)
            callsign: New callsign (for set_callsign)

        Returns:
            JSON string with result
        """
        logger.info(f"BBS session tool: action={action}, connection={connection_id}, callsign={callsign}")

        try:
            if action == "get_session_info":
                return self._get_session_info(connection_id)
            elif action == "get_callsign":
                return self._get_callsign(connection_id)
            elif action == "set_callsign":
                return self._set_callsign(connection_id, callsign)
            elif action == "list_users":
                return self._list_users()
            elif action == "get_help":
                return self._get_help()
            elif action == "get_status":
                return self._get_status()
            elif action == "clear_history":
                return self._clear_history(connection_id)
            elif action == "disconnect":
                return self._disconnect(connection_id)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown action: {action}"
                })

        except Exception as e:
            logger.error(f"BBS session tool error: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def _get_session_info(self, connection_id: Optional[str]) -> str:
        """Get detailed session information for a connection"""
        if not connection_id:
            return json.dumps({
                "success": False,
                "error": "connection_id is required"
            })

        # Get session from session manager
        session = self.app.session_manager.get_session(connection_id)

        # Get connection info
        conn_info = self._find_connection(connection_id)

        result = {
            "success": True,
            "session": {
                "callsign": session.callsign,
                "messages": len(session.messages),
                "queries": session.query_count,
                "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
                "last_activity": datetime.fromtimestamp(session.last_activity).isoformat(),
                "idle_seconds": int(session.get_idle_time()),
                "age_seconds": int(session.get_age())
            }
        }

        if conn_info:
            result["connection"] = conn_info

        return json.dumps(result, indent=2)

    def _get_callsign(self, connection_id: Optional[str]) -> str:
        """Get callsign for a connection"""
        if not connection_id:
            return json.dumps({
                "success": False,
                "error": "connection_id is required"
            })

        conn_info = self._find_connection(connection_id)
        if not conn_info:
            return json.dumps({
                "success": False,
                "error": f"Connection not found: {connection_id}"
            })

        return json.dumps({
            "success": True,
            "callsign": conn_info.get("callsign", connection_id),
            "connection_type": conn_info.get("type")
        })

    def _set_callsign(self, connection_id: Optional[str], callsign: Optional[str]) -> str:
        """Set callsign for a telnet connection"""
        if not connection_id:
            return json.dumps({
                "success": False,
                "error": "connection_id is required"
            })

        if not callsign:
            return json.dumps({
                "success": False,
                "error": "callsign parameter is required"
            })

        # Only works for telnet connections
        if not self.app.telnet_server:
            return json.dumps({
                "success": False,
                "error": "Telnet server not enabled"
            })

        # Find the telnet connection
        for conn in self.app.telnet_server.get_all_connections():
            if conn.remote_address == connection_id or conn._remote_address == connection_id:
                old_callsign = conn.remote_address
                conn.set_callsign(callsign)

                # Update connections dictionary
                if conn._remote_address in self.app.telnet_server.connections:
                    del self.app.telnet_server.connections[conn._remote_address]
                    self.app.telnet_server.connections[conn.remote_address] = conn

                return json.dumps({
                    "success": True,
                    "message": f"Callsign updated from {old_callsign} to {callsign}",
                    "old_callsign": old_callsign,
                    "new_callsign": callsign
                })

        return json.dumps({
            "success": False,
            "error": f"Telnet connection not found: {connection_id}"
        })

    def _list_users(self) -> str:
        """List all connected users"""
        users = []

        # Add AX.25 connections
        if self.app.connection_handler:
            for conn in self.app.connection_handler.connections.values():
                users.append({
                    "callsign": conn.remote_address,
                    "type": "ax25",
                    "state": conn.state.value,
                    "connected_at": datetime.fromtimestamp(conn.connected_at).isoformat() if conn.connected_at else None,
                    "packets_sent": conn.packets_sent,
                    "packets_received": conn.packets_received
                })

        # Add telnet connections
        if self.app.telnet_server:
            for conn in self.app.telnet_server.get_all_connections():
                users.append({
                    "callsign": conn.remote_address,
                    "type": "telnet",
                    "state": conn.state.value,
                    "connected_at": datetime.fromtimestamp(conn.connected_at).isoformat(),
                    "packets_sent": conn.packets_sent,
                    "packets_received": conn.packets_received,
                    "ip_address": conn._remote_address
                })

        return json.dumps({
            "success": True,
            "total_users": len(users),
            "users": users
        }, indent=2)

    def _get_help(self) -> str:
        """Get help information"""
        help_text = {
            "success": True,
            "help": {
                "bbs_commands": {
                    "help": "Display available commands",
                    "status": "Show system status and your session info",
                    "bye/quit/exit": "Disconnect from the BBS",
                    "clear": "Clear your conversation history"
                },
                "claude_interaction": {
                    "description": "Ask Claude anything! Just type your question.",
                    "examples": [
                        "what is amateur radio?",
                        "show me pota spots on 20m",
                        "explain how the ionosphere works"
                    ]
                },
                "tools": {
                    "web_search": "Claude can search the internet for current information",
                    "pota_spots": "Claude can fetch live Parks on the Air activations",
                    "bbs_session": "Claude can help with BBS system commands"
                },
                "notes": [
                    "PacketClaude is an AI-powered packet radio BBS",
                    "All conversations are logged for quality assurance",
                    "Rate limits apply to prevent abuse",
                    "Your callsign is used to maintain conversation context"
                ]
            }
        }
        return json.dumps(help_text, indent=2)

    def _get_status(self) -> str:
        """Get system status"""
        stats = self.app.session_manager.get_stats()

        # Count connections
        ax25_connections = len(self.app.connection_handler.connections) if self.app.connection_handler else 0
        telnet_connections = len(self.app.telnet_server.get_all_connections()) if self.app.telnet_server else 0

        status = {
            "success": True,
            "system": {
                "name": "PacketClaude",
                "description": "AX.25 Packet Radio Gateway for Claude AI",
                "version": "1.0",
                "uptime_seconds": int(self.app.session_manager.get_active_sessions()[0].get_age()) if self.app.session_manager.get_session_count() > 0 else 0
            },
            "interfaces": {
                "ax25_enabled": self.app.connection_handler is not None,
                "telnet_enabled": self.app.telnet_server is not None,
                "ax25_connections": ax25_connections,
                "telnet_connections": telnet_connections,
                "total_connections": ax25_connections + telnet_connections
            },
            "sessions": {
                "active_sessions": stats['active_sessions'],
                "total_messages": stats['total_messages'],
                "total_queries": stats['total_queries']
            },
            "tools": {
                "web_search": self.app.config.search_enabled,
                "pota_spots": self.app.config.pota_enabled
            }
        }

        return json.dumps(status, indent=2)

    def _clear_history(self, connection_id: Optional[str]) -> str:
        """Clear conversation history for a user"""
        if not connection_id:
            return json.dumps({
                "success": False,
                "error": "connection_id is required"
            })

        self.app.session_manager.clear_session(connection_id)

        return json.dumps({
            "success": True,
            "message": f"Conversation history cleared for {connection_id}"
        })

    def _disconnect(self, connection_id: Optional[str]) -> str:
        """Disconnect a user (gracefully)"""
        if not connection_id:
            return json.dumps({
                "success": False,
                "error": "connection_id is required"
            })

        # Find and disconnect
        disconnected = False

        # Check AX.25 connections
        if self.app.connection_handler:
            for conn in self.app.connection_handler.connections.values():
                if conn.remote_address == connection_id:
                    self.app.connection_handler.disconnect(conn)
                    disconnected = True
                    break

        # Check telnet connections
        if not disconnected and self.app.telnet_server:
            for conn in self.app.telnet_server.get_all_connections():
                if conn.remote_address == connection_id or conn._remote_address == connection_id:
                    self.app.telnet_server.disconnect(conn)
                    disconnected = True
                    break

        if disconnected:
            return json.dumps({
                "success": True,
                "message": f"Disconnected {connection_id}"
            })
        else:
            return json.dumps({
                "success": False,
                "error": f"Connection not found: {connection_id}"
            })

    def _find_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Find connection by ID and return info"""
        # Check AX.25 connections
        if self.app.connection_handler:
            for conn in self.app.connection_handler.connections.values():
                if conn.remote_address == connection_id:
                    return {
                        "type": "ax25",
                        "callsign": conn.remote_address,
                        "state": conn.state.value,
                        "connected_at": datetime.fromtimestamp(conn.connected_at).isoformat() if conn.connected_at else None,
                        "packets_sent": conn.packets_sent,
                        "packets_received": conn.packets_received
                    }

        # Check telnet connections
        if self.app.telnet_server:
            for conn in self.app.telnet_server.get_all_connections():
                if conn.remote_address == connection_id or conn._remote_address == connection_id:
                    return {
                        "type": "telnet",
                        "callsign": conn.remote_address,
                        "state": conn.state.value,
                        "connected_at": datetime.fromtimestamp(conn.connected_at).isoformat(),
                        "packets_sent": conn.packets_sent,
                        "packets_received": conn.packets_received,
                        "ip_address": conn._remote_address
                    }

        return None
