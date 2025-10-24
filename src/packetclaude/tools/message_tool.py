"""
Message tool for Claude
Allows users to send, read, list, and delete messages (BBS-style mail)
"""
import logging
import json
from typing import Dict, Optional
from datetime import datetime
from ..utils import normalize_callsign

logger = logging.getLogger(__name__)


class MessageTool:
    """
    BBS messaging tool for Claude
    Provides email-like functionality for packet radio users
    """

    def __init__(self, database, enabled: bool = True):
        """
        Initialize message tool

        Args:
            database: Database instance for message storage
            enabled: Enable/disable messaging functionality
        """
        self.database = database
        self.enabled = enabled

    def get_tool_definition(self) -> Dict:
        """
        Get Claude API tool definition for messaging

        Returns:
            Tool definition dictionary
        """
        return {
            "name": "messages",
            "description": (
                "Interact with the BBS message system. Users can send messages to other callsigns, "
                "list their received messages, list their sent messages, read specific messages, "
                "delete messages, and reply to messages. This is like email for packet radio operators. "
                "Use this when users ask about mail, messages, outbox, sent messages, or want to "
                "communicate with other users."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "read", "send", "delete", "reply"],
                        "description": "The action to perform"
                    },
                    "callsign": {
                        "type": "string",
                        "description": "User's callsign (required for all actions)"
                    },
                    "message_id": {
                        "type": "integer",
                        "description": "Message ID (required for read, delete, reply actions)"
                    },
                    "to_callsign": {
                        "type": "string",
                        "description": "Recipient callsign (required for send action)"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Message subject (optional for send action - will be generated from body if omitted)"
                    },
                    "body": {
                        "type": "string",
                        "description": "Message body (required for send and reply actions)"
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "For list action: only show unread messages (default: false)"
                    },
                    "sent": {
                        "type": "boolean",
                        "description": "For list action: show sent messages instead of received (default: false)"
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
        if tool_name == "messages":
            action = tool_input.get("action")
            callsign = normalize_callsign(tool_input.get("callsign", ""))

            if not callsign:
                return json.dumps({
                    "error": "Missing parameter",
                    "message": "Callsign is required"
                })

            if action == "list":
                unread_only = tool_input.get("unread_only", False)
                sent = tool_input.get("sent", False)
                return self._list_messages(callsign, unread_only, sent)
            elif action == "read":
                message_id = tool_input.get("message_id")
                if not message_id:
                    return json.dumps({"error": "message_id required for read action"})
                return self._read_message(callsign, message_id)
            elif action == "send":
                to_callsign = normalize_callsign(tool_input.get("to_callsign", ""))
                subject = tool_input.get("subject", "")
                body = tool_input.get("body", "")
                if not to_callsign or not body:
                    return json.dumps({"error": "to_callsign and body required for send action"})
                # Generate subject from body if not provided
                if not subject:
                    subject = self._generate_subject(body)
                return self._send_message(callsign, to_callsign, subject, body)
            elif action == "delete":
                message_id = tool_input.get("message_id")
                if not message_id:
                    return json.dumps({"error": "message_id required for delete action"})
                return self._delete_message(callsign, message_id)
            elif action == "reply":
                message_id = tool_input.get("message_id")
                body = tool_input.get("body", "")
                if not message_id or not body:
                    return json.dumps({"error": "message_id and body required for reply action"})
                return self._reply_to_message(callsign, message_id, body)
            else:
                return json.dumps({"error": f"Unknown action: {action}"})
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for BBS display"""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return timestamp

    def _generate_subject(self, body: str) -> str:
        """Generate a subject line from message body"""
        # Take first line or first 50 chars, whichever is shorter
        lines = body.strip().split('\n')
        first_line = lines[0] if lines else body

        # Truncate to 50 chars
        subject = first_line[:50].strip()

        # Add ellipsis if truncated
        if len(first_line) > 50:
            subject += "..."

        return subject if subject else "(no subject)"

    def _list_messages(self, callsign: str, unread_only: bool, sent: bool = False) -> str:
        """List messages for a callsign"""
        try:
            logger.info(f"Listing messages for {callsign} (unread_only={unread_only}, sent={sent})")

            if sent:
                messages = self.database.get_sent_messages(callsign)
                unread_count = 0  # Sent messages don't have unread count
            else:
                messages = self.database.get_messages(callsign, unread_only=unread_only)
                unread_count = self.database.get_unread_count(callsign)

            if not messages:
                if sent:
                    return json.dumps({
                        "success": True,
                        "message": "No sent messages.",
                        "total_count": 0,
                        "messages": []
                    })
                elif unread_only:
                    return json.dumps({
                        "success": True,
                        "message": "No unread messages.",
                        "unread_count": 0,
                        "total_count": 0,
                        "messages": []
                    })
                else:
                    return json.dumps({
                        "success": True,
                        "message": "No messages.",
                        "unread_count": 0,
                        "total_count": 0,
                        "messages": []
                    })

            # Format for BBS-style listing
            message_list = []
            for msg in messages:
                if sent:
                    # For sent messages, show "to" instead of "from" and read status
                    status = "R" if msg['is_read'] else " "
                    message_list.append({
                        "id": msg['id'],
                        "status": status,
                        "to": msg['to'],
                        "subject": msg['subject'],
                        "date": self._format_timestamp(msg['created_at']),
                        "is_read": msg['is_read']
                    })
                else:
                    # For received messages, show "from" and new status
                    status = "N" if not msg['is_read'] else " "
                    message_list.append({
                        "id": msg['id'],
                        "status": status,
                        "from": msg['from'],
                        "subject": msg['subject'],
                        "date": self._format_timestamp(msg['created_at']),
                        "is_read": msg['is_read']
                    })

            result = {
                "success": True,
                "total_count": len(messages),
                "messages": message_list
            }

            if not sent:
                result["unread_count"] = unread_count

            return json.dumps(result)

        except Exception as e:
            logger.error(f"Error listing messages: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to list messages",
                "message": str(e)
            })

    def _read_message(self, callsign: str, message_id: int) -> str:
        """Read a specific message"""
        try:
            logger.info(f"Reading message {message_id} for {callsign}")

            message = self.database.get_message(message_id, callsign)

            if not message:
                return json.dumps({
                    "error": "Message not found",
                    "message": f"Message {message_id} not found or you don't have permission to read it"
                })

            # Mark as read if it's to this user and unread
            if message['to'] == callsign and not message['is_read']:
                self.database.mark_message_read(message_id, callsign)
                message['is_read'] = True

            # Format for BBS display
            return json.dumps({
                "success": True,
                "message": {
                    "id": message['id'],
                    "from": message['from'],
                    "to": message['to'],
                    "subject": message['subject'],
                    "body": message['body'],
                    "date": self._format_timestamp(message['created_at']),
                    "is_read": message['is_read'],
                    "in_reply_to": message['in_reply_to']
                }
            })

        except Exception as e:
            logger.error(f"Error reading message: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to read message",
                "message": str(e)
            })

    def _send_message(self, from_callsign: str, to_callsign: str,
                     subject: str, body: str, in_reply_to: Optional[int] = None) -> str:
        """Send a message"""
        try:
            logger.info(f"Sending message from {from_callsign} to {to_callsign}: {subject}")

            message_id = self.database.send_message(
                from_callsign, to_callsign, subject, body, in_reply_to
            )

            return json.dumps({
                "success": True,
                "message_id": message_id,
                "message": f"Message sent to {to_callsign}."
            })

        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to send message",
                "message": str(e)
            })

    def _delete_message(self, callsign: str, message_id: int) -> str:
        """Delete a message"""
        try:
            logger.info(f"Deleting message {message_id} for {callsign}")

            success = self.database.delete_message(message_id, callsign)

            if success:
                return json.dumps({
                    "success": True,
                    "message": f"Message {message_id} deleted."
                })
            else:
                return json.dumps({
                    "error": "Delete failed",
                    "message": f"Message {message_id} not found or already deleted"
                })

        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to delete message",
                "message": str(e)
            })

    def _reply_to_message(self, callsign: str, message_id: int, body: str) -> str:
        """Reply to a message"""
        try:
            logger.info(f"Replying to message {message_id} from {callsign}")

            # Get the original message
            original = self.database.get_message(message_id, callsign)

            if not original:
                return json.dumps({
                    "error": "Message not found",
                    "message": f"Message {message_id} not found or you don't have permission"
                })

            # Determine reply recipient (if we received it, reply to sender)
            if original['to'] == callsign:
                to_callsign = original['from']
            else:
                to_callsign = original['to']

            # Create reply subject
            subject = original['subject']
            if not subject.startswith('Re: '):
                subject = f"Re: {subject}"

            # Send the reply
            new_message_id = self.database.send_message(
                callsign, to_callsign, subject, body, in_reply_to=message_id
            )

            return json.dumps({
                "success": True,
                "message_id": new_message_id,
                "message": f"Reply sent to {to_callsign}."
            })

        except Exception as e:
            logger.error(f"Error replying to message: {e}", exc_info=True)
            return json.dumps({
                "error": "Failed to send reply",
                "message": str(e)
            })
