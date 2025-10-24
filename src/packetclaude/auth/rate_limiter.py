"""
Rate limiting for packet radio access
"""
import logging
import re
from typing import Optional, Tuple
from ..database import Database


logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter for controlling query frequency per callsign
    """

    def __init__(self, database: Database,
                 queries_per_hour: int = 10,
                 queries_per_day: int = 50,
                 enabled: bool = True):
        """
        Initialize rate limiter

        Args:
            database: Database instance for tracking
            queries_per_hour: Maximum queries per hour per callsign
            queries_per_day: Maximum queries per day per callsign
            enabled: Enable rate limiting
        """
        self.database = database
        self.queries_per_hour = queries_per_hour
        self.queries_per_day = queries_per_day
        self.enabled = enabled

    def check_limit(self, callsign: str) -> Tuple[bool, Optional[str]]:
        """
        Check if callsign is within rate limits

        Args:
            callsign: Station callsign

        Returns:
            Tuple of (allowed: bool, reason: str if not allowed)
        """
        if not self.enabled:
            return True, None

        # Validate callsign format first
        if not self.is_valid_callsign(callsign):
            return False, "Invalid callsign format"

        # Check database for rate limits
        allowed, reason = self.database.check_rate_limit(
            callsign.upper(),
            self.queries_per_hour,
            self.queries_per_day
        )

        if not allowed:
            logger.warning(f"Rate limit exceeded for {callsign}: {reason}")

        return allowed, reason

    def get_status(self, callsign: str) -> dict:
        """
        Get rate limit status for callsign

        Args:
            callsign: Station callsign

        Returns:
            Dictionary with rate limit information
        """
        if not self.enabled:
            return {
                'enabled': False,
                'message': 'Rate limiting disabled'
            }

        status = self.database.get_rate_limit_status(
            callsign.upper(),
            self.queries_per_hour,
            self.queries_per_day
        )

        status['enabled'] = True
        return status

    @staticmethod
    def is_valid_callsign(callsign: str) -> bool:
        """
        Validate amateur radio callsign format

        Args:
            callsign: Callsign to validate

        Returns:
            True if valid format
        """
        # Basic callsign validation
        # Format: 1-2 characters, digit, 1-4 characters, optional -SSID
        pattern = r'^[A-Z0-9]{1,2}[0-9][A-Z0-9]{1,4}(-[0-9]{1,2})?$'

        callsign_upper = callsign.upper().strip()
        match = re.match(pattern, callsign_upper)

        return match is not None

    def format_limit_message(self, status: dict) -> str:
        """
        Format rate limit status as a friendly message

        Args:
            status: Status dictionary from get_status()

        Returns:
            Formatted message string
        """
        if not status.get('enabled'):
            return "Rate limiting is disabled."

        msg = f"Rate limits:\n"
        msg += f"Hourly: {status['hourly_used']}/{status['hourly_limit']} "
        msg += f"({status['hourly_remaining']} remaining)\n"
        msg += f"Daily: {status['daily_used']}/{status['daily_limit']} "
        msg += f"({status['daily_remaining']} remaining)"

        return msg


class CallsignValidator:
    """
    Validates and normalizes amateur radio callsigns
    """

    @staticmethod
    def normalize(callsign: str) -> str:
        """
        Normalize callsign to standard format

        Args:
            callsign: Raw callsign string

        Returns:
            Normalized callsign (uppercase, trimmed)
        """
        return callsign.upper().strip()

    @staticmethod
    def parse(callsign: str) -> Tuple[str, int]:
        """
        Parse callsign into base callsign and SSID

        Args:
            callsign: Callsign string (e.g., "N0CALL-10")

        Returns:
            Tuple of (base_callsign, ssid)
        """
        normalized = CallsignValidator.normalize(callsign)

        if '-' in normalized:
            parts = normalized.split('-', 1)
            base = parts[0]
            try:
                ssid = int(parts[1])
            except ValueError:
                ssid = 0
            return base, ssid
        else:
            return normalized, 0

    @staticmethod
    def format(callsign: str, ssid: int = 0) -> str:
        """
        Format callsign with SSID

        Args:
            callsign: Base callsign
            ssid: SSID (0-15)

        Returns:
            Formatted callsign string
        """
        callsign_upper = callsign.upper().strip()
        if ssid > 0:
            return f"{callsign_upper}-{ssid}"
        return callsign_upper

    @staticmethod
    def is_valid(callsign: str) -> bool:
        """
        Validate callsign format

        Args:
            callsign: Callsign to validate

        Returns:
            True if valid
        """
        return RateLimiter.is_valid_callsign(callsign)
