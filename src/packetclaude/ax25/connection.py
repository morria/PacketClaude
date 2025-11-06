"""
AX.25 connection handler
Manages connected-mode AX.25 sessions with multiple clients
"""
import logging
import time
from typing import Dict, Optional, Callable
from enum import Enum
from .protocol import AX25Frame, parse_callsign
from .kiss import KISSClient
from .yapp import YAPPManager, YAPPControl


logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """AX.25 connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"


class AX25Connection:
    """Represents a single AX.25 connection"""

    def __init__(self, remote_callsign: str, remote_ssid: int,
                 local_callsign: str, local_ssid: int):
        """
        Initialize connection

        Args:
            remote_callsign: Remote station callsign
            remote_ssid: Remote station SSID
            local_callsign: Local station callsign
            local_ssid: Local station SSID
        """
        self.remote_callsign = remote_callsign
        self.remote_ssid = remote_ssid
        self.local_callsign = local_callsign
        self.local_ssid = local_ssid
        self.state = ConnectionState.DISCONNECTED
        self.connected_at: Optional[float] = None
        self.last_activity: float = time.time()
        self.packets_sent = 0
        self.packets_received = 0
        self.in_yapp_mode = False  # Flag for YAPP file transfer mode

    @property
    def remote_address(self) -> str:
        """Get remote address string"""
        if self.remote_ssid:
            return f"{self.remote_callsign}-{self.remote_ssid}"
        return self.remote_callsign

    @property
    def local_address(self) -> str:
        """Get local address string"""
        if self.local_ssid:
            return f"{self.local_callsign}-{self.local_ssid}"
        return self.local_callsign

    def __str__(self):
        return f"{self.remote_address} ({self.state.value})"


class AX25ConnectionHandler:
    """
    Handles multiple AX.25 connections
    """

    def __init__(self, kiss_client: KISSClient,
                 local_callsign: str,
                 local_ssid: int = 10):
        """
        Initialize connection handler

        Args:
            kiss_client: KISS client for sending/receiving frames
            local_callsign: Local station callsign
            local_ssid: Local station SSID
        """
        self.kiss_client = kiss_client
        self.local_callsign = local_callsign.upper()
        self.local_ssid = local_ssid

        # Active connections: key is "CALLSIGN-SSID"
        self.connections: Dict[str, AX25Connection] = {}

        # Callbacks
        self.on_connect: Optional[Callable[[AX25Connection], None]] = None
        self.on_disconnect: Optional[Callable[[AX25Connection], None]] = None
        self.on_data: Optional[Callable[[AX25Connection, bytes], None]] = None
        self.on_yapp_data: Optional[Callable[[AX25Connection, bytes], None]] = None

        # YAPP manager
        self.yapp_manager = YAPPManager()

    def handle_incoming_frame(self, frame: AX25Frame):
        """
        Handle an incoming AX.25 frame

        Args:
            frame: Received AX.25 frame
        """
        # Check if frame is addressed to us
        if frame.destination.callsign.strip() != self.local_callsign:
            return

        remote_key = f"{frame.source.callsign.strip()}-{frame.source.ssid}"

        # Handle SABM (connection request)
        if frame.is_sabm_frame():
            self._handle_sabm(frame, remote_key)

        # Handle DISC (disconnect request)
        elif frame.is_disc_frame():
            self._handle_disc(frame, remote_key)

        # Handle UI frame (unnumbered information - connectionless)
        elif frame.is_ui_frame():
            self._handle_ui(frame, remote_key)

        # Handle data in connected mode
        else:
            self._handle_data(frame, remote_key)

    def _handle_sabm(self, frame: AX25Frame, remote_key: str):
        """Handle SABM (connection request)"""
        logger.info(f"Connection request from {remote_key}")

        # Create or update connection
        # Use the destination SSID from the incoming frame so we respond as the callsign they connected to
        if remote_key not in self.connections:
            conn = AX25Connection(
                frame.source.callsign.strip(),
                frame.source.ssid,
                frame.destination.callsign.strip(),  # Use destination from frame
                frame.destination.ssid  # Use destination SSID from frame
            )
            self.connections[remote_key] = conn
        else:
            conn = self.connections[remote_key]

        # Update state
        conn.state = ConnectionState.CONNECTED
        conn.connected_at = time.time()
        conn.last_activity = time.time()

        # Send UA (Unnumbered Acknowledge) - respond as the callsign they connected to
        ua_frame = AX25Frame.create_ua_frame(
            frame.source.callsign.strip(),
            frame.destination.callsign.strip(),  # Respond as destination
            frame.source.ssid,
            frame.destination.ssid  # Use destination SSID
        )
        self._send_frame(ua_frame)

        # Notify callback
        if self.on_connect:
            self.on_connect(conn)

    def _handle_disc(self, frame: AX25Frame, remote_key: str):
        """Handle DISC (disconnect request)"""
        logger.info(f"Disconnect request from {remote_key}")

        # Send UA (acknowledge) - respond as the callsign they disconnected from
        ua_frame = AX25Frame.create_ua_frame(
            frame.source.callsign.strip(),
            frame.destination.callsign.strip(),  # Respond as destination
            frame.source.ssid,
            frame.destination.ssid  # Use destination SSID
        )
        self._send_frame(ua_frame)

        # Handle disconnection
        if remote_key in self.connections:
            conn = self.connections[remote_key]
            conn.state = ConnectionState.DISCONNECTED

            # Notify callback
            if self.on_disconnect:
                self.on_disconnect(conn)

            # Remove connection
            del self.connections[remote_key]

    def _handle_ui(self, frame: AX25Frame, remote_key: str):
        """Handle UI frame (connectionless data)"""
        # UI frames are connectionless, but we can still process them
        # Create a temporary connection object if needed
        if remote_key not in self.connections:
            conn = AX25Connection(
                frame.source.callsign.strip(),
                frame.source.ssid,
                frame.destination.callsign.strip(),  # Use destination from frame
                frame.destination.ssid  # Use destination SSID from frame
            )
            # Don't add to connections dict for UI frames
        else:
            conn = self.connections[remote_key]

        conn.last_activity = time.time()
        conn.packets_received += 1

        # Notify callback
        if self.on_data and frame.info:
            self.on_data(conn, frame.info)

    def _handle_data(self, frame: AX25Frame, remote_key: str):
        """Handle data frame in connected mode"""
        if remote_key not in self.connections:
            # No connection exists, send DM (respond as the destination they sent to)
            dm_frame = AX25Frame.create_dm_frame(
                frame.source.callsign.strip(),
                frame.destination.callsign.strip(),  # Respond as destination
                frame.source.ssid,
                frame.destination.ssid  # Use destination SSID
            )
            self._send_frame(dm_frame)
            return

        conn = self.connections[remote_key]

        if conn.state != ConnectionState.CONNECTED:
            # Not connected, ignore or send DM
            return

        conn.last_activity = time.time()
        conn.packets_received += 1

        # Check if this is YAPP data
        if frame.info and self._is_yapp_packet(frame.info):
            # Handle YAPP packet
            conn.in_yapp_mode = True
            if self.on_yapp_data:
                self.on_yapp_data(conn, frame.info)
        # Notify callback if there's data
        elif self.on_data and frame.info:
            self.on_data(conn, frame.info)

    def send_data(self, connection: AX25Connection, data: bytes) -> bool:
        """
        Send data to a connected station

        Args:
            connection: Active connection
            data: Data to send

        Returns:
            True if successful
        """
        if connection.state != ConnectionState.CONNECTED:
            logger.error(f"Cannot send data: {connection} not connected")
            return False

        # Create UI frame for simplicity (connectionless)
        # In a full implementation, would use I frames
        frame = AX25Frame.create_ui_frame(
            connection.remote_callsign,
            connection.local_callsign,  # Use connection's local callsign
            data,
            connection.remote_ssid,
            connection.local_ssid  # Use connection's local SSID
        )

        if self._send_frame(frame):
            connection.packets_sent += 1
            connection.last_activity = time.time()
            return True

        return False

    def disconnect(self, connection: AX25Connection):
        """
        Disconnect from a station

        Args:
            connection: Connection to disconnect
        """
        if connection.state == ConnectionState.DISCONNECTED:
            return

        # Send DISC frame using connection's local callsign
        disc_frame = AX25Frame.create_disc_frame(
            connection.remote_callsign,
            connection.local_callsign,  # Use connection's local callsign
            connection.remote_ssid,
            connection.local_ssid  # Use connection's local SSID
        )
        self._send_frame(disc_frame)

        connection.state = ConnectionState.DISCONNECTING

        # Will be removed when we receive UA

    def _send_frame(self, frame: AX25Frame) -> bool:
        """
        Send an AX.25 frame via KISS

        Args:
            frame: Frame to send

        Returns:
            True if successful
        """
        try:
            encoded = frame.encode()
            return self.kiss_client.send_frame(encoded)
        except Exception as e:
            logger.error(f"Failed to send frame: {e}")
            return False

    def get_connection(self, remote_callsign: str,
                      remote_ssid: int = 0) -> Optional[AX25Connection]:
        """
        Get connection by callsign

        Args:
            remote_callsign: Remote station callsign
            remote_ssid: Remote station SSID

        Returns:
            Connection object or None
        """
        key = f"{remote_callsign.upper()}-{remote_ssid}"
        return self.connections.get(key)

    def get_all_connections(self) -> list[AX25Connection]:
        """Get list of all active connections"""
        return list(self.connections.values())

    def cleanup_stale_connections(self, timeout: int = 300):
        """
        Remove connections that have been inactive

        Args:
            timeout: Inactivity timeout in seconds
        """
        now = time.time()
        stale = []

        for key, conn in self.connections.items():
            if now - conn.last_activity > timeout:
                stale.append(key)

        for key in stale:
            conn = self.connections[key]
            logger.info(f"Removing stale connection: {conn}")

            if self.on_disconnect:
                self.on_disconnect(conn)

            del self.connections[key]

        # Cleanup YAPP timeouts
        self.yapp_manager.cleanup_timeouts()

    def _is_yapp_packet(self, data: bytes) -> bool:
        """
        Check if data appears to be a YAPP packet

        Args:
            data: Packet data

        Returns:
            True if YAPP packet
        """
        if not data:
            return False

        # Check for YAPP control characters
        yapp_controls = {
            YAPPControl.ENQ, YAPPControl.ACK, YAPPControl.NAK,
            YAPPControl.SOH, YAPPControl.STX, YAPPControl.ETX,
            YAPPControl.EOT, YAPPControl.CAN
        }

        return data[0] in yapp_controls

    def start_yapp_upload(self, connection: AX25Connection) -> bool:
        """
        Start receiving a file via YAPP

        Args:
            connection: Connection to receive from

        Returns:
            True if started successfully
        """
        response = self.yapp_manager.start_upload(connection.remote_address)
        if response:
            connection.in_yapp_mode = True
            return self.send_data(connection, response)
        return False

    def start_yapp_download(self, connection: AX25Connection,
                           filename: str, file_data: bytes) -> bool:
        """
        Start sending a file via YAPP

        Args:
            connection: Connection to send to
            filename: Filename
            file_data: File contents

        Returns:
            True if started successfully
        """
        response = self.yapp_manager.start_download(
            connection.remote_address,
            filename,
            file_data
        )
        if response:
            connection.in_yapp_mode = True
            return self.send_data(connection, response)
        return False

    def handle_yapp_packet(self, connection: AX25Connection, data: bytes) -> bool:
        """
        Handle YAPP packet and send response

        Args:
            connection: Connection
            data: YAPP packet data

        Returns:
            True if handled successfully
        """
        response = self.yapp_manager.handle_packet(connection.remote_address, data)
        if response:
            return self.send_data(connection, response)
        return True  # No response needed, but successfully handled

    def get_yapp_transfer(self, connection: AX25Connection):
        """
        Get active YAPP transfer for connection

        Args:
            connection: Connection

        Returns:
            YAPPTransfer object or None
        """
        return self.yapp_manager.get_transfer(connection.remote_address)

    def cancel_yapp_transfer(self, connection: AX25Connection) -> bool:
        """
        Cancel YAPP transfer

        Args:
            connection: Connection

        Returns:
            True if cancelled
        """
        response = self.yapp_manager.cancel_transfer(connection.remote_address)
        if response:
            connection.in_yapp_mode = False
            return self.send_data(connection, response)
        return False
