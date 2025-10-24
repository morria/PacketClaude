"""
Telnet server for PacketClaude
Provides TCP/telnet access for testing and debugging
"""
import socket
import threading
import logging
import time
from typing import Optional, Callable, Dict
from enum import Enum


logger = logging.getLogger(__name__)


# Telnet protocol constants (RFC 854, RFC 1572)
IAC = b'\xff'  # Interpret As Command
WILL = b'\xfb'
WONT = b'\xfc'
DO = b'\xfd'
DONT = b'\xfe'
SB = b'\xfa'  # Subnegotiation Begin
SE = b'\xf0'  # Subnegotiation End

# Telnet options
TELOPT_NEW_ENVIRON = b'\x27'  # RFC 1572 - New Environment Option


class ConnectionState(Enum):
    """Connection states"""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"


class TelnetConnection:
    """Represents a single telnet connection"""

    def __init__(self, client_socket: socket.socket, address: tuple):
        """
        Initialize telnet connection

        Args:
            client_socket: Client socket
            address: Client address (host, port)
        """
        self.socket = client_socket
        self.address = address
        self.state = ConnectionState.CONNECTED
        self.connected_at = time.time()
        self.last_activity = time.time()
        self.packets_sent = 0
        self.packets_received = 0
        self.connection_id: Optional[int] = None

        # Callsign detection
        self.callsign: Optional[str] = None  # Detected callsign from telnet login
        self._remote_address = f"{address[0]}:{address[1]}"  # Default identifier

    @property
    def remote_address(self) -> str:
        """Get remote address string - returns callsign if detected, otherwise IP:port"""
        return self.callsign if self.callsign else self._remote_address

    @property
    def local_address(self) -> str:
        """Get local address string (telnet server)"""
        return "TELNET"

    def send(self, data: bytes) -> bool:
        """
        Send data to client

        Args:
            data: Data to send

        Returns:
            True if successful
        """
        try:
            self.socket.sendall(data)
            self.packets_sent += 1
            self.last_activity = time.time()
            return True
        except Exception as e:
            logger.error(f"Error sending to {self.remote_address}: {e}")
            return False

    def close(self):
        """Close the connection"""
        try:
            self.socket.close()
            self.state = ConnectionState.DISCONNECTED
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    def set_callsign(self, callsign: str):
        """
        Set the callsign for this connection

        Args:
            callsign: User's callsign or login name
        """
        if callsign and callsign.strip():
            self.callsign = callsign.strip().upper()
            logger.info(f"Connection {self._remote_address} identified as {self.callsign}")

    def __str__(self):
        return f"{self.remote_address} ({self.state.value})"


class TelnetServer:
    """
    Telnet server for PacketClaude
    Allows TCP/telnet connections for testing
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8023):
        """
        Initialize telnet server

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.connections: Dict[str, TelnetConnection] = {}
        self.accept_thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_connect: Optional[Callable[[TelnetConnection], None]] = None
        self.on_disconnect: Optional[Callable[[TelnetConnection], None]] = None
        self.on_data: Optional[Callable[[TelnetConnection, bytes], None]] = None

    def start(self) -> bool:
        """
        Start the telnet server

        Returns:
            True if successful
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Allow periodic checks

            self.running = True

            # Start accept thread
            self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.accept_thread.start()

            logger.info(f"Telnet server listening on {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start telnet server: {e}")
            return False

    def stop(self):
        """Stop the telnet server"""
        logger.info("Stopping telnet server...")
        self.running = False

        # Close all connections
        for conn in list(self.connections.values()):
            self._handle_disconnect(conn)

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")

        # Wait for accept thread
        if self.accept_thread:
            self.accept_thread.join(timeout=2.0)

        logger.info("Telnet server stopped")

    def _accept_loop(self):
        """Accept incoming connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                logger.info(f"New telnet connection from {address}")

                # Create connection object
                conn = TelnetConnection(client_socket, address)

                # Request environment variables from client (RFC 1572)
                # This asks the client to send USER, LOGNAME, etc.
                try:
                    # IAC DO NEW-ENVIRON - ask client to send environment
                    client_socket.sendall(IAC + DO + TELOPT_NEW_ENVIRON)
                except Exception as e:
                    logger.warning(f"Could not request telnet environment: {e}")

                self.connections[conn._remote_address] = conn

                # Start receive thread for this connection
                recv_thread = threading.Thread(
                    target=self._receive_loop,
                    args=(conn,),
                    daemon=True
                )
                recv_thread.start()

                # Notify callback
                if self.on_connect:
                    self.on_connect(conn)

            except socket.timeout:
                # Normal timeout, continue
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")

    def _parse_telnet_data(self, conn: TelnetConnection, data: bytes) -> bytes:
        """
        Parse telnet protocol data and extract environment variables

        Args:
            conn: Connection receiving data
            data: Raw data from client

        Returns:
            Data with telnet protocol sequences removed
        """
        # Look for IAC sequences
        if IAC not in data:
            return data

        result = b""
        i = 0
        while i < len(data):
            if data[i:i+1] == IAC:
                if i + 1 < len(data):
                    cmd = data[i+1:i+2]

                    # Handle subnegotiation (SB ... SE)
                    if cmd == SB and i + 2 < len(data):
                        option = data[i+2:i+3]

                        # Find SE (end of subnegotiation)
                        se_pos = data.find(SE, i + 3)
                        if se_pos != -1:
                            if option == TELOPT_NEW_ENVIRON:
                                # Parse environment variables
                                env_data = data[i+3:se_pos]
                                self._parse_environ(conn, env_data)
                            i = se_pos + 1
                            continue

                    # Skip IAC commands (WILL, WONT, DO, DONT)
                    if cmd in (WILL, WONT, DO, DONT):
                        i += 3  # IAC + CMD + OPTION
                        continue

                    # Double IAC means literal 0xFF
                    if cmd == IAC:
                        result += IAC
                        i += 2
                        continue

                    i += 2
                else:
                    i += 1
            else:
                result += data[i:i+1]
                i += 1

        return result

    def _parse_environ(self, conn: TelnetConnection, env_data: bytes):
        """
        Parse NEW-ENVIRON subnegotiation data

        Args:
            conn: Connection
            env_data: Environment data from subnegotiation
        """
        # Environment variable format: VAR name VALUE value ...
        # VAR = 0, VALUE = 1, ESC = 2, USERVAR = 3
        VAR = 0
        VALUE = 1

        i = 0
        while i < len(env_data):
            if env_data[i] == VAR or env_data[i] == 3:  # VAR or USERVAR
                # Read variable name
                i += 1
                name_start = i
                while i < len(env_data) and env_data[i] not in (VAR, VALUE, 2, 3):
                    i += 1
                var_name = env_data[name_start:i].decode('ascii', errors='ignore')

                # Read value if present
                var_value = ""
                if i < len(env_data) and env_data[i] == VALUE:
                    i += 1
                    value_start = i
                    while i < len(env_data) and env_data[i] not in (VAR, VALUE, 2, 3):
                        i += 1
                    var_value = env_data[value_start:i].decode('ascii', errors='ignore')

                # Check if this is a login name variable
                if var_name.upper() in ('USER', 'LOGNAME') and var_value:
                    logger.info(f"Detected telnet login for {conn._remote_address}: {var_value}")
                    conn.set_callsign(var_value)

                    # Update connection key in dictionary
                    if conn._remote_address in self.connections:
                        del self.connections[conn._remote_address]
                        self.connections[conn.remote_address] = conn
                    break
            else:
                i += 1

    def _receive_loop(self, conn: TelnetConnection):
        """
        Receive data from a connection

        Args:
            conn: Connection to receive from
        """
        buffer = b""

        try:
            while self.running and conn.state == ConnectionState.CONNECTED:
                try:
                    # Receive data
                    data = conn.socket.recv(4096)

                    if not data:
                        # Connection closed
                        break

                    # Parse telnet protocol data
                    data = self._parse_telnet_data(conn, data)

                    buffer += data
                    conn.last_activity = time.time()

                    # Process line by line
                    while b'\n' in buffer or b'\r' in buffer:
                        # Split on newline or carriage return
                        if b'\r\n' in buffer:
                            line, buffer = buffer.split(b'\r\n', 1)
                        elif b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                        elif b'\r' in buffer:
                            line, buffer = buffer.split(b'\r', 1)
                        else:
                            break

                        if line:
                            conn.packets_received += 1

                            # Notify callback
                            if self.on_data:
                                self.on_data(conn, line)

                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving from {conn.remote_address}: {e}")
                    break

        finally:
            self._handle_disconnect(conn)

    def _handle_disconnect(self, conn: TelnetConnection):
        """
        Handle connection disconnect

        Args:
            conn: Connection that disconnected
        """
        if conn.remote_address in self.connections:
            logger.info(f"Telnet disconnection from {conn.remote_address}")

            # Notify callback
            if self.on_disconnect:
                self.on_disconnect(conn)

            # Close and remove
            conn.close()
            del self.connections[conn.remote_address]

    def send_data(self, conn: TelnetConnection, data: bytes) -> bool:
        """
        Send data to a connection

        Args:
            conn: Connection to send to
            data: Data to send

        Returns:
            True if successful
        """
        if conn.state != ConnectionState.CONNECTED:
            logger.error(f"Cannot send data: {conn} not connected")
            return False

        return conn.send(data)

    def disconnect(self, conn: TelnetConnection):
        """
        Disconnect a connection

        Args:
            conn: Connection to disconnect
        """
        if conn.state == ConnectionState.DISCONNECTED:
            return

        conn.state = ConnectionState.DISCONNECTING
        self._handle_disconnect(conn)

    def get_all_connections(self) -> list:
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
            logger.info(f"Removing stale telnet connection: {conn}")
            self._handle_disconnect(conn)
