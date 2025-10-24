"""
AX.25 protocol implementation
Handles parsing and building AX.25 frames

Reference: AX.25 v2.2 specification
"""
import struct
import logging
from typing import Optional, List, Tuple
from enum import IntEnum


logger = logging.getLogger(__name__)


class AX25FrameType(IntEnum):
    """AX.25 frame types"""
    I_FRAME = 0  # Information frame
    S_FRAME = 1  # Supervisory frame
    U_FRAME = 2  # Unnumbered frame


class AX25UFrameType(IntEnum):
    """Unnumbered frame types"""
    SABM = 0x2F  # Set Async Balanced Mode
    SABME = 0x6F  # SABM Extended
    DISC = 0x43  # Disconnect
    DM = 0x0F  # Disconnect Mode
    UA = 0x63  # Unnumbered Acknowledge
    FRMR = 0x87  # Frame Reject
    UI = 0x03  # Unnumbered Information
    XID = 0xAF  # Exchange Identification
    TEST = 0xE3  # Test


class AX25Address:
    """AX.25 address (callsign + SSID)"""

    def __init__(self, callsign: str, ssid: int = 0,
                 command_response: bool = False,
                 reserved_bits: int = 0x03):
        """
        Initialize AX.25 address

        Args:
            callsign: Amateur radio callsign (up to 6 characters)
            ssid: Secondary Station Identifier (0-15)
            command_response: C/R bit
            reserved_bits: Reserved bits (usually 0x03 for 1.1 compatibility)
        """
        self.callsign = callsign.upper()[:6].ljust(6)
        self.ssid = ssid & 0x0F
        self.command_response = command_response
        self.reserved_bits = reserved_bits & 0x03

    def encode(self, last: bool = False) -> bytes:
        """
        Encode address to AX.25 format

        Args:
            last: True if this is the last address in the header

        Returns:
            7-byte encoded address
        """
        # Each callsign character is shifted left 1 bit
        encoded = bytearray()
        for char in self.callsign:
            encoded.append(ord(char) << 1)

        # SSID byte: [C/R][reserved1][reserved0][SSID3][SSID2][SSID1][SSID0][last]
        ssid_byte = (self.command_response << 7) | \
                   (self.reserved_bits << 5) | \
                   (self.ssid << 1) | \
                   (1 if last else 0)
        encoded.append(ssid_byte)

        return bytes(encoded)

    @staticmethod
    def decode(data: bytes) -> 'AX25Address':
        """
        Decode AX.25 address from bytes

        Args:
            data: 7-byte encoded address

        Returns:
            AX25Address object
        """
        if len(data) < 7:
            raise ValueError("Address must be 7 bytes")

        # Decode callsign (shift right 1 bit)
        callsign = ''.join(chr(b >> 1) for b in data[:6]).strip()

        # Decode SSID byte
        ssid_byte = data[6]
        command_response = bool(ssid_byte & 0x80)
        reserved_bits = (ssid_byte >> 5) & 0x03
        ssid = (ssid_byte >> 1) & 0x0F

        return AX25Address(callsign, ssid, command_response, reserved_bits)

    def __str__(self):
        """String representation"""
        if self.ssid:
            return f"{self.callsign.strip()}-{self.ssid}"
        return self.callsign.strip()

    def __repr__(self):
        return f"AX25Address('{self}')"


class AX25Frame:
    """AX.25 frame"""

    def __init__(self,
                 destination: AX25Address,
                 source: AX25Address,
                 digipeaters: List[AX25Address] = None,
                 control: int = 0x03,
                 pid: int = 0xF0,
                 info: bytes = b''):
        """
        Initialize AX.25 frame

        Args:
            destination: Destination address
            source: Source address
            digipeaters: List of digipeater addresses
            control: Control field
            pid: Protocol ID (for I and UI frames)
            info: Information field
        """
        self.destination = destination
        self.source = source
        self.digipeaters = digipeaters or []
        self.control = control
        self.pid = pid
        self.info = info

    def encode(self) -> bytes:
        """
        Encode frame to bytes

        Returns:
            Encoded AX.25 frame
        """
        frame = bytearray()

        # Destination address
        frame.extend(self.destination.encode(last=False))

        # Source address (last if no digipeaters)
        last = len(self.digipeaters) == 0
        frame.extend(self.source.encode(last=last))

        # Digipeater addresses
        for i, digi in enumerate(self.digipeaters):
            last = (i == len(self.digipeaters) - 1)
            frame.extend(digi.encode(last=last))

        # Control field
        frame.append(self.control)

        # PID (for I and UI frames)
        if self._is_info_frame():
            frame.append(self.pid)

        # Information field
        if self.info:
            frame.extend(self.info)

        return bytes(frame)

    @staticmethod
    def decode(data: bytes) -> 'AX25Frame':
        """
        Decode AX.25 frame from bytes

        Args:
            data: Encoded frame data

        Returns:
            AX25Frame object
        """
        if len(data) < 16:  # Minimum: dest(7) + source(7) + control(1) + pid(1)
            raise ValueError("Frame too short")

        offset = 0

        # Decode destination
        destination = AX25Address.decode(data[offset:offset+7])
        offset += 7

        # Decode source
        source = AX25Address.decode(data[offset:offset+7])
        offset += 7

        # Decode digipeaters
        digipeaters = []
        while offset < len(data) and not (data[offset - 1] & 0x01):
            if offset + 7 > len(data):
                break
            digi = AX25Address.decode(data[offset:offset+7])
            digipeaters.append(digi)
            offset += 7

        # Control field
        if offset >= len(data):
            raise ValueError("No control field")
        control = data[offset]
        offset += 1

        # PID and info
        pid = 0xF0
        info = b''

        # Check if this is an info frame (I or UI)
        if control & 0x01 == 0 or control == 0x03:
            if offset < len(data):
                pid = data[offset]
                offset += 1
            if offset < len(data):
                info = data[offset:]

        return AX25Frame(destination, source, digipeaters, control, pid, info)

    def _is_info_frame(self) -> bool:
        """Check if this is an information frame (I or UI)"""
        return (self.control & 0x01 == 0) or (self.control == 0x03)

    def get_frame_type(self) -> AX25FrameType:
        """Get frame type"""
        if self.control & 0x01 == 0:
            return AX25FrameType.I_FRAME
        elif self.control & 0x02 == 0:
            return AX25FrameType.S_FRAME
        else:
            return AX25FrameType.U_FRAME

    def is_ui_frame(self) -> bool:
        """Check if this is a UI (Unnumbered Information) frame"""
        return self.control == 0x03

    def is_sabm_frame(self) -> bool:
        """Check if this is a SABM (Set Async Balanced Mode) frame"""
        return (self.control & 0xEF) == 0x2F

    def is_disc_frame(self) -> bool:
        """Check if this is a DISC (Disconnect) frame"""
        return (self.control & 0xEF) == 0x43

    def is_ua_frame(self) -> bool:
        """Check if this is a UA (Unnumbered Acknowledge) frame"""
        return (self.control & 0xEF) == 0x63

    def is_dm_frame(self) -> bool:
        """Check if this is a DM (Disconnect Mode) frame"""
        return (self.control & 0xEF) == 0x0F

    @staticmethod
    def create_ui_frame(destination: str, source: str,
                       info: bytes,
                       dest_ssid: int = 0,
                       source_ssid: int = 0) -> 'AX25Frame':
        """
        Create a UI (Unnumbered Information) frame

        Args:
            destination: Destination callsign
            source: Source callsign
            info: Information payload
            dest_ssid: Destination SSID
            source_ssid: Source SSID

        Returns:
            AX25Frame
        """
        return AX25Frame(
            destination=AX25Address(destination, dest_ssid),
            source=AX25Address(source, source_ssid),
            control=0x03,  # UI frame
            pid=0xF0,  # No layer 3
            info=info
        )

    @staticmethod
    def create_sabm_frame(destination: str, source: str,
                         dest_ssid: int = 0,
                         source_ssid: int = 0) -> 'AX25Frame':
        """
        Create a SABM (Set Async Balanced Mode) frame

        Args:
            destination: Destination callsign
            source: Source callsign
            dest_ssid: Destination SSID
            source_ssid: Source SSID

        Returns:
            AX25Frame
        """
        return AX25Frame(
            destination=AX25Address(destination, dest_ssid),
            source=AX25Address(source, source_ssid),
            control=0x3F,  # SABM with P bit set
            pid=0xF0,
            info=b''
        )

    @staticmethod
    def create_ua_frame(destination: str, source: str,
                       dest_ssid: int = 0,
                       source_ssid: int = 0) -> 'AX25Frame':
        """
        Create a UA (Unnumbered Acknowledge) frame

        Args:
            destination: Destination callsign
            source: Source callsign
            dest_ssid: Destination SSID
            source_ssid: Source SSID

        Returns:
            AX25Frame
        """
        return AX25Frame(
            destination=AX25Address(destination, dest_ssid),
            source=AX25Address(source, source_ssid),
            control=0x73,  # UA with F bit set
            pid=0xF0,
            info=b''
        )

    @staticmethod
    def create_disc_frame(destination: str, source: str,
                         dest_ssid: int = 0,
                         source_ssid: int = 0) -> 'AX25Frame':
        """
        Create a DISC (Disconnect) frame

        Args:
            destination: Destination callsign
            source: Source callsign
            dest_ssid: Destination SSID
            source_ssid: Source SSID

        Returns:
            AX25Frame
        """
        return AX25Frame(
            destination=AX25Address(destination, dest_ssid),
            source=AX25Address(source, source_ssid),
            control=0x53,  # DISC with P bit set
            pid=0xF0,
            info=b''
        )

    @staticmethod
    def create_dm_frame(destination: str, source: str,
                       dest_ssid: int = 0,
                       source_ssid: int = 0) -> 'AX25Frame':
        """
        Create a DM (Disconnect Mode) frame

        Args:
            destination: Destination callsign
            source: Source callsign
            dest_ssid: Destination SSID
            source_ssid: Source SSID

        Returns:
            AX25Frame
        """
        return AX25Frame(
            destination=AX25Address(destination, dest_ssid),
            source=AX25Address(source, source_ssid),
            control=0x1F,  # DM with F bit set
            pid=0xF0,
            info=b''
        )

    def __str__(self):
        """String representation"""
        frame_type = "UNKNOWN"
        if self.is_ui_frame():
            frame_type = "UI"
        elif self.is_sabm_frame():
            frame_type = "SABM"
        elif self.is_disc_frame():
            frame_type = "DISC"
        elif self.is_ua_frame():
            frame_type = "UA"
        elif self.is_dm_frame():
            frame_type = "DM"

        return f"{self.source} -> {self.destination} [{frame_type}]"

    def __repr__(self):
        return f"AX25Frame({self})"


def parse_callsign(callsign_str: str) -> Tuple[str, int]:
    """
    Parse callsign string into callsign and SSID

    Args:
        callsign_str: Callsign string (e.g., "N0CALL-10")

    Returns:
        Tuple of (callsign, ssid)
    """
    if '-' in callsign_str:
        parts = callsign_str.split('-')
        callsign = parts[0].strip().upper()
        try:
            ssid = int(parts[1])
        except ValueError:
            ssid = 0
        return callsign, ssid
    else:
        return callsign_str.strip().upper(), 0
