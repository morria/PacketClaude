"""
Session management for per-callsign Claude conversations
"""
import logging
import time
from typing import Dict, List, Optional, Any
from collections import deque


logger = logging.getLogger(__name__)


class ConversationSession:
    """
    Represents a conversation session for a single user
    """

    def __init__(self, callsign: str, max_messages: int = 20):
        """
        Initialize session

        Args:
            callsign: User callsign
            max_messages: Maximum messages to keep in history
        """
        self.callsign = callsign
        self.max_messages = max_messages
        self.messages: deque = deque(maxlen=max_messages)
        self.created_at = time.time()
        self.last_activity = time.time()
        self.query_count = 0
        self.authenticated = False
        self.operator_info: Optional[Dict] = None

    def add_message(self, role: str, content: str):
        """
        Add a message to conversation history

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        self.messages.append({
            "role": role,
            "content": content
        })
        self.last_activity = time.time()
        if role == "user":
            self.query_count += 1

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history

        Returns:
            List of messages
        """
        return list(self.messages)

    def clear(self):
        """Clear conversation history"""
        self.messages.clear()
        logger.info(f"Cleared conversation history for {self.callsign}")

    def authenticate(self, operator_info: Dict[str, Any]):
        """
        Mark session as authenticated and store operator info

        Args:
            operator_info: Operator information from QRZ lookup
        """
        self.authenticated = True
        self.operator_info = operator_info
        logger.info(f"Session authenticated for {self.callsign}: {operator_info.get('fullname', 'Unknown')}")

    def get_age(self) -> float:
        """
        Get session age in seconds

        Returns:
            Age in seconds
        """
        return time.time() - self.created_at

    def get_idle_time(self) -> float:
        """
        Get idle time in seconds

        Returns:
            Idle time in seconds
        """
        return time.time() - self.last_activity

    def __str__(self):
        return f"{self.callsign} ({len(self.messages)} messages, {self.query_count} queries)"


class SessionManager:
    """
    Manages conversation sessions for multiple users
    """

    def __init__(self, max_messages_per_session: int = 20):
        """
        Initialize session manager

        Args:
            max_messages_per_session: Maximum messages to keep per session
        """
        self.max_messages = max_messages_per_session
        self.sessions: Dict[str, ConversationSession] = {}

    def get_session(self, callsign: str) -> ConversationSession:
        """
        Get or create session for callsign

        Args:
            callsign: User callsign

        Returns:
            ConversationSession
        """
        callsign_upper = callsign.upper()

        if callsign_upper not in self.sessions:
            logger.info(f"Creating new session for {callsign_upper}")
            self.sessions[callsign_upper] = ConversationSession(
                callsign_upper,
                self.max_messages
            )

        return self.sessions[callsign_upper]

    def add_user_message(self, callsign: str, message: str):
        """
        Add user message to session

        Args:
            callsign: User callsign
            message: User message
        """
        session = self.get_session(callsign)
        session.add_message("user", message)

    def add_assistant_message(self, callsign: str, message: str):
        """
        Add assistant message to session

        Args:
            callsign: User callsign
            message: Assistant message
        """
        session = self.get_session(callsign)
        session.add_message("assistant", message)

    def get_history(self, callsign: str) -> List[Dict[str, str]]:
        """
        Get conversation history for callsign

        Args:
            callsign: User callsign

        Returns:
            List of messages
        """
        session = self.get_session(callsign)
        return session.get_history()

    def clear_session(self, callsign: str):
        """
        Clear session for callsign

        Args:
            callsign: User callsign
        """
        callsign_upper = callsign.upper()
        if callsign_upper in self.sessions:
            self.sessions[callsign_upper].clear()

    def remove_session(self, callsign: str):
        """
        Remove session completely

        Args:
            callsign: User callsign
        """
        callsign_upper = callsign.upper()
        if callsign_upper in self.sessions:
            del self.sessions[callsign_upper]
            logger.info(f"Removed session for {callsign_upper}")

    def cleanup_idle_sessions(self, timeout: int = 300):
        """
        Remove sessions that have been idle

        Args:
            timeout: Idle timeout in seconds
        """
        to_remove = []

        for callsign, session in self.sessions.items():
            if session.get_idle_time() > timeout:
                to_remove.append(callsign)

        for callsign in to_remove:
            logger.info(f"Removing idle session: {callsign}")
            del self.sessions[callsign]

    def get_active_sessions(self) -> List[ConversationSession]:
        """
        Get list of all active sessions

        Returns:
            List of sessions
        """
        return list(self.sessions.values())

    def get_session_count(self) -> int:
        """
        Get number of active sessions

        Returns:
            Number of sessions
        """
        return len(self.sessions)

    def get_stats(self) -> Dict[str, any]:
        """
        Get statistics about sessions

        Returns:
            Dictionary with statistics
        """
        total_messages = sum(len(s.messages) for s in self.sessions.values())
        total_queries = sum(s.query_count for s in self.sessions.values())

        return {
            'active_sessions': len(self.sessions),
            'total_messages': total_messages,
            'total_queries': total_queries,
        }
