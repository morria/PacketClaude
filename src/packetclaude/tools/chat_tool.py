"""
Chat tool for Claude
Multi-user chat channels (like CB Simulator or conference mode on classic BBSes)
"""
import logging
import json
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatTool:
    """
    BBS chat system tool for Claude
    Provides real-time chat channels for packet radio users
    """

    def __init__(self, database, enabled: bool = True):
        """
        Initialize chat tool

        Args:
            database: Database instance for chat storage
            enabled: Enable/disable chat functionality
        """
        self.database = database
        self.enabled = enabled

    def get_tool_definition(self) -> Dict:
        """
        Get Claude API tool definition for chat

        Returns:
            Tool definition dictionary
        """
        return {
            "name": "chat",
            "description": (
                "Multi-user chat system for the BBS. Users can join channels, send messages, "
                "see who's online, list channels, and create new channels. Like CB Simulator or "
                "conference mode on classic BBSes. Use this when users want to chat, talk to others, "
                "join a channel, see who's online, or use commands like /C, /JOIN, /WHO, /CHAT."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["join", "leave", "send", "list_channels", "who", "recent", "topic"],
                        "description": "The action to perform"
                    },
                    "callsign": {
                        "type": "string",
                        "description": "User's callsign (required for all actions)"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Channel name (required for join, leave, send, who, recent, topic actions). Use 'MAIN' for the main public channel."
                    },
                    "message": {
                        "type": "string",
                        "description": "Message text (required for send action)"
                    },
                    "topic": {
                        "type": "string",
                        "description": "New channel topic (required for topic action)"
                    }
                },
                "required": ["action", "callsign"]
            }
        }

    def execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """
        Execute tool call from Claude

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters

        Returns:
            JSON string with results
        """
        if tool_name == "chat":
            action = tool_input.get("action")
            callsign = tool_input.get("callsign", "").upper()

            if not callsign:
                return json.dumps({
                    "error": "Missing parameter",
                    "message": "Callsign is required"
                })

            if action == "join":
                channel = tool_input.get("channel", "").upper()
                if not channel:
                    return json.dumps({"error": "channel required for join action"})
                return self._join_channel(callsign, channel)

            elif action == "leave":
                channel = tool_input.get("channel", "").upper()
                if not channel:
                    # Leave all channels
                    return self._leave_all_channels(callsign)
                return self._leave_channel(callsign, channel)

            elif action == "send":
                channel = tool_input.get("channel", "").upper()
                message = tool_input.get("message", "")
                if not channel or not message:
                    return json.dumps({"error": "channel and message required for send action"})
                return self._send_message(callsign, channel, message)

            elif action == "list_channels":
                return self._list_channels(callsign)

            elif action == "who":
                channel = tool_input.get("channel", "").upper()
                if not channel:
                    return json.dumps({"error": "channel required for who action"})
                return self._who(channel)

            elif action == "recent":
                channel = tool_input.get("channel", "").upper()
                if not channel:
                    return json.dumps({"error": "channel required for recent action"})
                return self._recent_messages(channel)

            elif action == "topic":
                channel = tool_input.get("channel", "").upper()
                topic = tool_input.get("topic", "")
                if not channel:
                    return json.dumps({"error": "channel required for topic action"})
                return self._set_topic(channel, topic)

            else:
                return json.dumps({"error": f"Unknown action: {action}"})
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for BBS display (HH:MM)"""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%H:%M")
        except:
            return timestamp

    def _join_channel(self, callsign: str, channel_name: str) -> str:
        """Join a chat channel"""
        try:
            logger.info(f"{callsign} joining channel {channel_name}")

            # Get or create channel
            channel_id = self.database.get_or_create_channel(channel_name, callsign)

            # Add user to channel
            self.database.join_channel(channel_id, callsign)

            # Get channel info
            channel_info = self.database.get_channel_by_name(channel_name)

            # Get recent messages (last 4 from last 24 hours)
            recent = self.database.get_recent_messages(channel_id, limit=4, hours=24)

            # Get user list
            users = self.database.get_channel_users(channel_id)

            result = {
                "success": True,
                "message": f"Joined channel {channel_name}",
                "channel": {
                    "name": channel_name,
                    "topic": channel_info.get('topic'),
                    "users_online": len(users),
                    "users": users
                },
                "recent_messages": []
            }

            # Format recent messages
            for msg in recent:
                result["recent_messages"].append({
                    "callsign": msg['callsign'],
                    "message": msg['message'],
                    "time": self._format_timestamp(msg['timestamp'])
                })

            return json.dumps(result)

        except Exception as e:
            logger.error(f"Error joining channel: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to join channel",
                "message": str(e)
            })

    def _leave_channel(self, callsign: str, channel_name: str) -> str:
        """Leave a chat channel"""
        try:
            logger.info(f"{callsign} leaving channel {channel_name}")

            channel_info = self.database.get_channel_by_name(channel_name)
            if not channel_info:
                return json.dumps({
                    "error": "Channel not found",
                    "message": f"Channel {channel_name} does not exist"
                })

            self.database.leave_channel(channel_info['id'], callsign)

            return json.dumps({
                "success": True,
                "message": f"Left channel {channel_name}"
            })

        except Exception as e:
            logger.error(f"Error leaving channel: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to leave channel",
                "message": str(e)
            })

    def _leave_all_channels(self, callsign: str) -> str:
        """Leave all chat channels"""
        try:
            logger.info(f"{callsign} leaving all channels")

            self.database.leave_all_channels(callsign)

            return json.dumps({
                "success": True,
                "message": "Left all channels"
            })

        except Exception as e:
            logger.error(f"Error leaving all channels: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to leave channels",
                "message": str(e)
            })

    def _send_message(self, callsign: str, channel_name: str, message: str) -> str:
        """Send a message to a channel"""
        try:
            logger.info(f"{callsign} sending message to {channel_name}")

            channel_info = self.database.get_channel_by_name(channel_name)
            if not channel_info:
                return json.dumps({
                    "error": "Channel not found",
                    "message": f"Channel {channel_name} does not exist. Join it first with /JOIN {channel_name}"
                })

            # Check if user is in channel
            users = self.database.get_channel_users(channel_info['id'])
            if callsign not in users:
                return json.dumps({
                    "error": "Not in channel",
                    "message": f"You must join {channel_name} first. Use /JOIN {channel_name}"
                })

            # Post message
            self.database.post_chat_message(channel_info['id'], callsign, message)

            return json.dumps({
                "success": True,
                "message": f"Message sent to {channel_name}"
            })

        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to send message",
                "message": str(e)
            })

    def _list_channels(self, callsign: str) -> str:
        """List all chat channels"""
        try:
            logger.info(f"{callsign} listing channels")

            channels = self.database.list_channels()
            user_channels = self.database.get_user_channels(callsign)
            user_channel_ids = {ch['id'] for ch in user_channels}

            channel_list = []
            for ch in channels:
                channel_list.append({
                    "name": ch['channel_name'],
                    "topic": ch['topic'],
                    "users": ch['user_count'],
                    "joined": ch['id'] in user_channel_ids
                })

            return json.dumps({
                "success": True,
                "total_channels": len(channels),
                "channels": channel_list
            })

        except Exception as e:
            logger.error(f"Error listing channels: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to list channels",
                "message": str(e)
            })

    def _who(self, channel_name: str) -> str:
        """List users in a channel"""
        try:
            logger.info(f"Getting user list for {channel_name}")

            channel_info = self.database.get_channel_by_name(channel_name)
            if not channel_info:
                return json.dumps({
                    "error": "Channel not found",
                    "message": f"Channel {channel_name} does not exist"
                })

            users = self.database.get_channel_users(channel_info['id'])

            return json.dumps({
                "success": True,
                "channel": channel_name,
                "users": users,
                "count": len(users)
            })

        except Exception as e:
            logger.error(f"Error getting user list: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to get user list",
                "message": str(e)
            })

    def _recent_messages(self, channel_name: str) -> str:
        """Get recent messages from a channel"""
        try:
            logger.info(f"Getting recent messages from {channel_name}")

            channel_info = self.database.get_channel_by_name(channel_name)
            if not channel_info:
                return json.dumps({
                    "error": "Channel not found",
                    "message": f"Channel {channel_name} does not exist"
                })

            recent = self.database.get_recent_messages(channel_info['id'], limit=10, hours=24)

            messages = []
            for msg in recent:
                messages.append({
                    "callsign": msg['callsign'],
                    "message": msg['message'],
                    "time": self._format_timestamp(msg['timestamp'])
                })

            return json.dumps({
                "success": True,
                "channel": channel_name,
                "messages": messages
            })

        except Exception as e:
            logger.error(f"Error getting recent messages: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to get messages",
                "message": str(e)
            })

    def _set_topic(self, channel_name: str, topic: str) -> str:
        """Set channel topic"""
        try:
            logger.info(f"Setting topic for {channel_name}: {topic}")

            channel_info = self.database.get_channel_by_name(channel_name)
            if not channel_info:
                return json.dumps({
                    "error": "Channel not found",
                    "message": f"Channel {channel_name} does not exist"
                })

            self.database.set_channel_topic(channel_info['id'], topic)

            return json.dumps({
                "success": True,
                "message": f"Topic set for {channel_name}"
            })

        except Exception as e:
            logger.error(f"Error setting topic: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to set topic",
                "message": str(e)
            })
