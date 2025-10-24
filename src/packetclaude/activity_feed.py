"""
Activity feed for PacketClaude
Tracks recent user activities for display on connection
"""
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading

logger = logging.getLogger(__name__)


class ActivityFeed:
    """
    Tracks recent BBS activities for display
    Maintains an in-memory feed of recent actions
    """

    def __init__(self, max_items: int = 50):
        """
        Initialize activity feed

        Args:
            max_items: Maximum number of activities to track
        """
        self.max_items = max_items
        self.activities = deque(maxlen=max_items)
        self.lock = threading.Lock()

    def add_activity(self, callsign: str, action: str, details: str = ""):
        """
        Add an activity to the feed

        Args:
            callsign: Callsign of user performing action
            action: Type of action (query, lookup, message, pota, etc.)
            details: Optional details about the action
        """
        with self.lock:
            activity = {
                'callsign': callsign,
                'action': action,
                'details': details,
                'timestamp': datetime.now()
            }
            self.activities.append(activity)
            logger.debug(f"Activity added: {callsign} {action} {details}")

    def get_recent_summary(self, max_items: int = 3, max_age_minutes: int = 60) -> str:
        """
        Get a one-line summary of recent activities

        Args:
            max_items: Maximum number of activities to include
            max_age_minutes: Only include activities from last N minutes

        Returns:
            One-line summary string
        """
        with self.lock:
            if not self.activities:
                return "No recent activity"

            cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
            recent = [a for a in self.activities if a['timestamp'] >= cutoff]

            if not recent:
                return "No recent activity"

            # Take most recent items
            items = list(reversed(recent))[:max_items]

            # Format each activity
            formatted = []
            for item in items:
                age = datetime.now() - item['timestamp']
                age_str = self._format_age(age)

                action_desc = self._format_action(item['action'], item['details'])
                formatted.append(f"{item['callsign']} {action_desc} {age_str}")

            return "Recent: " + ", ".join(formatted)

    def _format_action(self, action: str, details: str) -> str:
        """Format action type into readable string"""
        action_map = {
            'query': 'asked a question',
            'lookup': f'looked up {details}' if details else 'looked up callsign',
            'message_sent': 'sent a message',
            'message_read': 'read mail',
            'pota': 'got POTA spots',
            'search': 'searched the web',
            'connect': 'connected',
            'disconnect': 'disconnected'
        }
        return action_map.get(action, action)

    def _format_age(self, age: timedelta) -> str:
        """Format time delta into readable string"""
        seconds = int(age.total_seconds())

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = seconds // 60
            return f"{mins}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        else:
            days = seconds // 86400
            return f"{days}d ago"

    def get_activity_count(self, max_age_minutes: int = 60) -> int:
        """
        Get count of activities in last N minutes

        Args:
            max_age_minutes: Time window in minutes

        Returns:
            Count of activities
        """
        with self.lock:
            cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
            return sum(1 for a in self.activities if a['timestamp'] >= cutoff)

    def get_active_users(self, max_age_minutes: int = 10) -> List[str]:
        """
        Get list of callsigns active in last N minutes

        Args:
            max_age_minutes: Time window in minutes

        Returns:
            List of unique callsigns
        """
        with self.lock:
            cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
            recent = [a for a in self.activities if a['timestamp'] >= cutoff]
            return list(set(a['callsign'] for a in recent))
