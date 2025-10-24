"""
QRZ.com callsign lookup
Authenticates and looks up amateur radio callsigns
"""
import logging
import requests
import xml.etree.ElementTree as ET
from typing import Optional, Dict
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class QRZLookup:
    """
    QRZ.com XML API client for callsign lookups
    """

    def __init__(self, username: str = "", password: str = "", api_key: str = "", enabled: bool = True):
        """
        Initialize QRZ lookup client

        Args:
            username: QRZ.com username (for username/password auth)
            password: QRZ.com password (for username/password auth)
            api_key: QRZ.com API key (for API key auth - preferred)
            enabled: Whether QRZ lookup is enabled
        """
        self.username = username
        self.password = password
        self.api_key = api_key
        self.enabled = enabled
        self.session_key: Optional[str] = None
        self.session_expires: Optional[datetime] = None
        self.base_url = "https://xmldata.qrz.com/xml/current/"

        # Prefer API key if provided
        if self.api_key:
            logger.info("QRZ callsign lookup enabled (using API key)")
        elif self.username and self.password:
            logger.info("QRZ callsign lookup enabled (using username/password)")
        else:
            logger.warning("QRZ lookup disabled - no credentials provided")

    def _get_session_key(self) -> bool:
        """
        Get a session key from QRZ.com

        Returns:
            True if successful
        """
        if not self.enabled:
            logger.warning("QRZ lookup is disabled")
            return False

        try:
            # Request session key
            params = {
                'username': self.username,
                'password': self.password,
            }

            # Add API key if available (identifies XML Logbook subscription)
            if self.api_key:
                params['api'] = self.api_key

            logger.debug(f"Requesting QRZ session key for user: {self.username}")
            response = requests.get(self.base_url, params=params, timeout=10)

            if response.status_code != 200:
                logger.error(f"QRZ API returned status {response.status_code}")
                return False

            # Parse XML response
            root = ET.fromstring(response.content)

            # Check for session key
            session = root.find('.//Session')
            if session is None:
                logger.error("No Session element in QRZ response")
                return False

            key = session.find('Key')
            if key is not None and key.text:
                self.session_key = key.text
                # Session is valid for 24 hours
                self.session_expires = datetime.now() + timedelta(hours=24)
                logger.info("QRZ session key obtained successfully")
                return True

            # Check for error
            error = session.find('Error')
            if error is not None and error.text:
                logger.error(f"QRZ authentication error: {error.text}")
                return False

            logger.error("Could not extract session key from QRZ response")
            return False

        except requests.RequestException as e:
            logger.error(f"QRZ API request failed: {e}")
            return False
        except ET.ParseError as e:
            logger.error(f"Failed to parse QRZ XML response: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error getting QRZ session: {e}", exc_info=True)
            return False

    def _ensure_session(self) -> bool:
        """
        Ensure we have a valid session key

        Returns:
            True if we have a valid session
        """
        if not self.enabled:
            return False

        # Check if we need a new session key
        if self.session_key is None or self.session_expires is None:
            return self._get_session_key()

        # Check if session expired
        if datetime.now() >= self.session_expires:
            logger.info("QRZ session expired, requesting new key")
            return self._get_session_key()

        return True

    def lookup(self, callsign: str) -> Optional[Dict]:
        """
        Look up a callsign on QRZ.com

        Args:
            callsign: Amateur radio callsign to look up

        Returns:
            Dictionary with operator information, or None if not found/error
        """
        if not self.enabled:
            logger.debug("QRZ lookup disabled, skipping")
            return None

        try:
            # Ensure we have a valid session key
            if not self._ensure_session():
                logger.error("Could not establish QRZ session")
                return None

            # Build lookup params with session key
            params = {
                's': self.session_key,
                'callsign': callsign.upper(),
            }

            auth_method = "API key" if self.api_key else "username/password"
            logger.debug(f"Looking up callsign on QRZ ({auth_method}): {callsign}")

            response = requests.get(self.base_url, params=params, timeout=10)

            if response.status_code != 200:
                logger.error(f"QRZ API returned status {response.status_code}")
                return None

            # Parse XML response
            root = ET.fromstring(response.content)

            # Check for callsign data
            callsign_elem = root.find('.//Callsign')
            if callsign_elem is None:
                # Check for error
                error = root.find('.//Session/Error')
                if error is not None and error.text:
                    logger.warning(f"QRZ lookup error for {callsign}: {error.text}")
                else:
                    logger.info(f"Callsign not found on QRZ: {callsign}")
                return None

            # Extract operator information
            info = {}

            # Basic info
            for field in ['call', 'fname', 'name', 'addr1', 'addr2', 'state',
                         'zip', 'country', 'lat', 'lon', 'grid', 'email',
                         'class', 'expires', 'aliases', 'email']:
                elem = callsign_elem.find(field)
                if elem is not None and elem.text:
                    info[field] = elem.text

            # Construct full name
            fname = info.get('fname', '')
            name = info.get('name', '')
            if fname and name:
                info['fullname'] = f"{fname} {name}"
            elif fname:
                info['fullname'] = fname
            elif name:
                info['fullname'] = name

            logger.info(f"Successfully looked up {callsign} on QRZ: {info.get('fullname', 'Unknown')}")
            return info

        except requests.RequestException as e:
            logger.error(f"QRZ API request failed: {e}")
            return None
        except ET.ParseError as e:
            logger.error(f"Failed to parse QRZ XML response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error looking up callsign: {e}", exc_info=True)
            return None

    def validate_callsign(self, callsign: str) -> bool:
        """
        Validate that a callsign exists on QRZ.com

        Args:
            callsign: Callsign to validate

        Returns:
            True if callsign is valid and exists
        """
        if not self.enabled:
            # If QRZ is disabled, just do basic format validation
            import re
            pattern = r'^[A-Z0-9]{1,2}[0-9][A-Z0-9]{1,4}(-[0-9]{1,2})?$'
            return re.match(pattern, callsign.upper().strip()) is not None

        # Look up on QRZ
        info = self.lookup(callsign)
        return info is not None
