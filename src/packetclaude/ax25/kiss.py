"""
KISS protocol implementation for connecting to Direwolf TNC
KISS (Keep It Simple, Stupid) is a simple protocol for communicating with TNCs

Reference: http://www.ax25.net/kiss.aspx
"""
import socket
import logging
from typing import Optional, Callable
from enum import IntEnum


logger = logging.getLogger(__name__)


class KISSCommand(IntEnum):
    """KISS command codes"""
    DATA_FRAME = 0x00
    TX_DELAY = 0x01
    PERSISTENCE = 0x02
    SLOT_TIME = 0x03
    TX_TAIL = 0x04
    FULL_DUPLEX = 0x05
    SET_HARDWARE = 0x06
    RETURN = 0xFF


class KISSFrame:
    """KISS frame constants"""
    FEND = 0xC0  # Frame End
    FESC = 0xDB  # Frame Escape
    TFEND = 0xDC  # Transposed Frame End
    TFESC = 0xDD  # Transposed Frame Escape


class KISSClient:
    """
    KISS protocol client for connecting to Direwolf or other KISS TNCs
    """

    def __init__(self, host: str = 'localhost', port: int = 8001, timeout: int = 30):
        """
        Initialize KISS client

        Args:
            host: TNC host address
            port: TNC port number
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.frame_callback: Optional[Callable[[bytes], None]] = None

    def connect(self) -> bool:
        """
        Connect to KISS TNC

        Returns:
            True if successful
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Connected to KISS TNC at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to KISS TNC: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from KISS TNC"""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
            finally:
                self.socket = None
                self.connected = False
                logger.info("Disconnected from KISS TNC")

    def send_frame(self, frame: bytes, port: int = 0) -> bool:
        """
        Send a KISS frame

        Args:
            frame: AX.25 frame data
            port: KISS port number (0-15)

        Returns:
            True if successful
        """
        if not self.connected or not self.socket:
            logger.error("Not connected to KISS TNC")
            return False

        try:
            # Build KISS frame
            kiss_frame = self._build_kiss_frame(frame, port)
            self.socket.sendall(kiss_frame)
            logger.debug(f"Sent KISS frame ({len(frame)} bytes)")
            return True
        except Exception as e:
            logger.error(f"Failed to send KISS frame: {e}")
            return False

    def receive_frame(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """
        Receive a KISS frame (blocking)

        Args:
            timeout: Receive timeout in seconds (None = use socket default)

        Returns:
            AX.25 frame data or None if error/timeout
        """
        if not self.connected or not self.socket:
            logger.error("Not connected to KISS TNC")
            return None

        try:
            # Set temporary timeout if specified
            original_timeout = self.socket.gettimeout()
            if timeout is not None:
                self.socket.settimeout(timeout)

            # Read until we get a complete KISS frame
            frame = self._read_kiss_frame()

            # Restore original timeout
            if timeout is not None:
                self.socket.settimeout(original_timeout)

            if frame:
                logger.debug(f"Received KISS frame ({len(frame)} bytes)")

            return frame
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Failed to receive KISS frame: {e}")
            return None

    def _build_kiss_frame(self, data: bytes, port: int = 0) -> bytes:
        """
        Build a KISS frame from AX.25 data

        Args:
            data: AX.25 frame data
            port: KISS port number

        Returns:
            KISS-encoded frame
        """
        # Command byte: port and command
        cmd = (port << 4) | KISSCommand.DATA_FRAME

        # Escape special characters
        escaped = bytearray()
        for byte in data:
            if byte == KISSFrame.FEND:
                escaped.extend([KISSFrame.FESC, KISSFrame.TFEND])
            elif byte == KISSFrame.FESC:
                escaped.extend([KISSFrame.FESC, KISSFrame.TFESC])
            else:
                escaped.append(byte)

        # Build frame: FEND + CMD + DATA + FEND
        frame = bytearray([KISSFrame.FEND, cmd])
        frame.extend(escaped)
        frame.append(KISSFrame.FEND)

        return bytes(frame)

    def _read_kiss_frame(self) -> Optional[bytes]:
        """
        Read a KISS frame from socket

        Returns:
            Decoded AX.25 frame or None
        """
        # Wait for frame start (FEND)
        while True:
            byte = self.socket.recv(1)
            if not byte:
                return None
            if byte[0] == KISSFrame.FEND:
                break

        # Read command byte
        cmd_byte = self.socket.recv(1)
        if not cmd_byte:
            return None

        # Extract port and command
        # port = (cmd_byte[0] >> 4) & 0x0F
        # cmd = cmd_byte[0] & 0x0F

        # Read frame data until FEND
        frame_data = bytearray()
        escaped = False

        while True:
            byte = self.socket.recv(1)
            if not byte:
                return None

            byte_val = byte[0]

            if byte_val == KISSFrame.FEND:
                # End of frame
                break
            elif byte_val == KISSFrame.FESC:
                # Escape sequence
                escaped = True
            elif escaped:
                # Handle escaped character
                if byte_val == KISSFrame.TFEND:
                    frame_data.append(KISSFrame.FEND)
                elif byte_val == KISSFrame.TFESC:
                    frame_data.append(KISSFrame.FESC)
                else:
                    # Invalid escape sequence, add as-is
                    frame_data.append(byte_val)
                escaped = False
            else:
                frame_data.append(byte_val)

        return bytes(frame_data) if frame_data else None

    def set_tx_delay(self, delay: int, port: int = 0):
        """
        Set TX delay (time before transmitting)

        Args:
            delay: Delay in 10ms units (0-255)
            port: KISS port number
        """
        cmd = (port << 4) | KISSCommand.TX_DELAY
        frame = bytes([KISSFrame.FEND, cmd, delay & 0xFF, KISSFrame.FEND])
        if self.socket:
            self.socket.sendall(frame)

    def set_persistence(self, persistence: int, port: int = 0):
        """
        Set persistence parameter for CSMA

        Args:
            persistence: Persistence value (0-255)
            port: KISS port number
        """
        cmd = (port << 4) | KISSCommand.PERSISTENCE
        frame = bytes([KISSFrame.FEND, cmd, persistence & 0xFF, KISSFrame.FEND])
        if self.socket:
            self.socket.sendall(frame)

    def set_slot_time(self, slot_time: int, port: int = 0):
        """
        Set slot time for CSMA

        Args:
            slot_time: Slot time in 10ms units (0-255)
            port: KISS port number
        """
        cmd = (port << 4) | KISSCommand.SLOT_TIME
        frame = bytes([KISSFrame.FEND, cmd, slot_time & 0xFF, KISSFrame.FEND])
        if self.socket:
            self.socket.sendall(frame)

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
