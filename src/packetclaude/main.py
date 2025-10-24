"""
PacketClaude - Main application
AX.25 Packet Radio Gateway for Claude AI
"""
import signal
import sys
import time
import logging
import threading
from pathlib import Path
from typing import Optional

from .config import Config
from .database import Database
from .ax25.kiss import KISSClient
from .ax25.protocol import AX25Frame
from .ax25.connection import AX25ConnectionHandler, AX25Connection
from .telnet.server import TelnetServer, TelnetConnection
from .radio.hamlib_control import RadioControl, DummyRadioControl
from .claude.client import ClaudeClient
from .claude.session import SessionManager
from .auth.rate_limiter import RateLimiter
from .logging.activity_logger import setup_logging, ActivityLogger
from .tools.web_search import WebSearchTool
from .tools.pota_spots import POTASpotsTool


logger = logging.getLogger(__name__)


class PacketClaude:
    """
    Main PacketClaude application
    """

    def __init__(self,
                 config_path: Optional[str] = None,
                 telnet_only: bool = False,
                 kiss_only: bool = False,
                 telnet_port: Optional[int] = None,
                 telnet_host: Optional[str] = None,
                 direwolf_host: Optional[str] = None,
                 direwolf_port: Optional[int] = None):
        """
        Initialize PacketClaude

        Args:
            config_path: Path to config file
            telnet_only: Run in telnet-only mode (no KISS/Direwolf)
            kiss_only: Run in KISS-only mode (no telnet)
            telnet_port: Override telnet port
            telnet_host: Override telnet host
            direwolf_host: Override Direwolf host
            direwolf_port: Override Direwolf port
        """
        # Load configuration
        self.config = Config(config_path)

        # Store mode flags
        self.telnet_only = telnet_only
        self.kiss_only = kiss_only

        # Store overrides
        self._telnet_port_override = telnet_port
        self._telnet_host_override = telnet_host
        self._direwolf_host_override = direwolf_host
        self._direwolf_port_override = direwolf_port

        # Setup logging
        setup_logging(
            self.config.log_dir,
            log_level="INFO",
            log_format=self.config.log_format,
            console_output=True
        )

        logger.info("=" * 60)
        logger.info("PacketClaude - AX.25 Packet Radio Gateway for Claude AI")
        logger.info("=" * 60)

        # Initialize database
        self.database = Database(self.config.database_path)

        # Initialize activity logger
        self.activity_logger = ActivityLogger(logger, self.database)

        # Initialize components
        self.kiss_client: Optional[KISSClient] = None
        self.connection_handler: Optional[AX25ConnectionHandler] = None
        self.telnet_server: Optional[TelnetServer] = None
        self.radio_control: Optional[RadioControl] = None
        self.claude_client: Optional[ClaudeClient] = None
        self.session_manager: Optional[SessionManager] = None
        self.rate_limiter: Optional[RateLimiter] = None

        # Running flag
        self.running = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def start(self):
        """Start PacketClaude"""
        try:
            self._initialize_components()
            self._run()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            self.activity_logger.log_error("Fatal", str(e), exception=e)
        finally:
            self.stop()

    def _initialize_components(self):
        """Initialize all components"""
        logger.info("Initializing components...")

        # Determine which interfaces to enable
        enable_kiss = not self.telnet_only
        enable_telnet = (not self.kiss_only) and (self.config.telnet_enabled or self.telnet_only)

        # Log startup configuration
        self.activity_logger.log_startup({
            'mode': 'telnet-only' if self.telnet_only else ('kiss-only' if self.kiss_only else 'both'),
            'callsign': self.config.station_callsign,
            'kiss_enabled': enable_kiss,
            'direwolf_host': self._direwolf_host_override or self.config.direwolf_host if enable_kiss else None,
            'direwolf_port': self._direwolf_port_override or self.config.direwolf_port if enable_kiss else None,
            'telnet_enabled': enable_telnet,
            'telnet_host': self._telnet_host_override or self.config.telnet_host if enable_telnet else None,
            'telnet_port': self._telnet_port_override or self.config.telnet_port if enable_telnet else None,
            'radio_enabled': self.config.radio_enabled if enable_kiss else False,
            'rate_limit_enabled': self.config.rate_limit_enabled,
        })

        # Initialize KISS client (if enabled)
        if enable_kiss:
            direwolf_host = self._direwolf_host_override or self.config.direwolf_host
            direwolf_port = self._direwolf_port_override or self.config.direwolf_port

            logger.info(f"Connecting to Direwolf at {direwolf_host}:{direwolf_port}")
            self.kiss_client = KISSClient(
                host=direwolf_host,
                port=direwolf_port,
                timeout=self.config.direwolf_timeout
            )

            if not self.kiss_client.connect():
                raise RuntimeError(
                    f"Failed to connect to Direwolf KISS TNC at {direwolf_host}:{direwolf_port}\n"
                    f"Make sure Direwolf is running or use --telnet-only mode"
                )

            # Initialize connection handler
            callsign, ssid = self._parse_callsign(self.config.station_callsign)
            self.connection_handler = AX25ConnectionHandler(
                self.kiss_client,
                callsign,
                ssid
            )

            # Set up connection callbacks
            self.connection_handler.on_connect = self._on_connect
            self.connection_handler.on_disconnect = self._on_disconnect
            self.connection_handler.on_data = self._on_data
        else:
            logger.info("KISS/Direwolf connection disabled (telnet-only mode)")
            self.kiss_client = None
            self.connection_handler = None

        # Initialize telnet server
        if enable_telnet:
            telnet_host = self._telnet_host_override or self.config.telnet_host
            telnet_port = self._telnet_port_override or self.config.telnet_port

            logger.info(f"Starting telnet server on {telnet_host}:{telnet_port}")
            self.telnet_server = TelnetServer(
                host=telnet_host,
                port=telnet_port
            )

            # Set up telnet callbacks
            self.telnet_server.on_connect = self._on_connect
            self.telnet_server.on_disconnect = self._on_disconnect
            self.telnet_server.on_data = self._on_data

            if not self.telnet_server.start():
                error_msg = f"Failed to start telnet server on {telnet_host}:{telnet_port}"
                if self.telnet_only:
                    raise RuntimeError(error_msg + " (telnet-only mode requires telnet)")
                else:
                    logger.warning(error_msg + ", continuing without it")
                    self.telnet_server = None
        else:
            logger.info("Telnet server disabled (kiss-only mode)")
            self.telnet_server = None

        # Initialize radio control (only if KISS is enabled)
        if enable_kiss and self.config.radio_enabled:
            logger.info("Initializing radio control...")
            self.radio_control = RadioControl(
                model=self.config.radio_model,
                device=self.config.radio_device,
                baud=self.config.radio_baud,
                enabled=True
            )
            self.radio_control.connect()
        else:
            if enable_kiss:
                logger.info("Radio control disabled, using dummy control")
            else:
                logger.info("Radio control disabled (telnet-only mode)")
            self.radio_control = DummyRadioControl()

        # Initialize Claude client with tools
        logger.info("Initializing Claude API client...")

        # Initialize tools
        tools = []
        if self.config.search_enabled:
            logger.info("Web search enabled")
            search_tool = WebSearchTool(
                max_results=self.config.search_max_results,
                enabled=True
            )
            tools.append(search_tool)

        if self.config.pota_enabled:
            logger.info("POTA spots tool enabled")
            pota_tool = POTASpotsTool(
                enabled=True,
                max_spots=self.config.pota_max_spots
            )
            tools.append(pota_tool)

        self.claude_client = ClaudeClient(
            api_key=self.config.anthropic_api_key,
            model=self.config.claude_model,
            max_tokens=self.config.claude_max_tokens,
            temperature=self.config.claude_temperature,
            system_prompt=self.config.claude_system_prompt,
            tools=tools
        )

        # Initialize session manager
        self.session_manager = SessionManager(
            max_messages_per_session=self.config.max_context_messages
        )

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            database=self.database,
            queries_per_hour=self.config.rate_limit_per_hour,
            queries_per_day=self.config.rate_limit_per_day,
            enabled=self.config.rate_limit_enabled
        )

        logger.info("All components initialized successfully")
        self.running = True

    def _run(self):
        """Main run loop"""
        if self.kiss_client:
            logger.info(f"PacketClaude ready - listening as {self.config.station_callsign}")
        if self.telnet_server:
            logger.info(f"PacketClaude ready - telnet on {self.telnet_server.host}:{self.telnet_server.port}")
        logger.info("Press Ctrl+C to stop")

        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        cleanup_thread.start()

        # Main receive loop (only if KISS is enabled)
        if self.kiss_client:
            while self.running:
                try:
                    # Receive frame from KISS TNC
                    frame_data = self.kiss_client.receive_frame(timeout=1.0)

                    if frame_data:
                        try:
                            # Decode AX.25 frame
                            frame = AX25Frame.decode(frame_data)
                            logger.debug(f"Received frame: {frame}")

                            # Handle frame
                            self.connection_handler.handle_incoming_frame(frame)

                        except Exception as e:
                            logger.error(f"Error processing frame: {e}")
                            self.activity_logger.log_error("FrameProcessing", str(e), exception=e)

                except Exception as e:
                    logger.error(f"Error in receive loop: {e}")
                    time.sleep(1)  # Prevent tight loop on errors
        else:
            # Telnet-only mode - just keep running
            logger.info("Running in telnet-only mode (no KISS processing)")
            while self.running:
                time.sleep(1)

    def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.running:
            try:
                # Sleep for 60 seconds
                time.sleep(60)

                if not self.running:
                    break

                # Cleanup stale connections
                if self.connection_handler:
                    self.connection_handler.cleanup_stale_connections(
                        timeout=self.config.session_timeout if self.config.session_timeout > 0 else 300
                    )

                # Cleanup stale telnet connections
                if self.telnet_server:
                    self.telnet_server.cleanup_stale_connections(
                        timeout=self.config.session_timeout if self.config.session_timeout > 0 else 300
                    )

                # Cleanup idle sessions
                self.session_manager.cleanup_idle_sessions(
                    timeout=self.config.session_timeout if self.config.session_timeout > 0 else 300
                )

                # Cleanup old database data (keep 30 days)
                self.database.cleanup_old_data(days=30)

                # Log statistics
                stats = self.session_manager.get_stats()
                logger.debug(f"Active sessions: {stats['active_sessions']}")

            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def _on_connect(self, connection: AX25Connection):
        """Handle new connection"""
        logger.info(f"New connection from {connection.remote_address}")

        # Log connection to database
        connection_id = self.database.log_connection(connection.remote_address)
        connection.connection_id = connection_id

        self.activity_logger.log_connection(connection.remote_address, connection_id)

        # Send welcome message
        welcome = self.config.welcome_message + "\n"
        self._send_to_station(connection, welcome)

    def _on_disconnect(self, connection: AX25Connection):
        """Handle disconnection"""
        logger.info(f"Disconnection from {connection.remote_address}")

        # Log disconnection
        if hasattr(connection, 'connection_id'):
            self.database.log_disconnection(
                connection.connection_id,
                connection.packets_sent,
                connection.packets_received
            )

        # Calculate duration
        duration = None
        if connection.connected_at:
            duration = time.time() - connection.connected_at

        self.activity_logger.log_disconnection(
            connection.remote_address,
            getattr(connection, 'connection_id', None),
            duration
        )

        # Remove session if configured
        if self.config.session_timeout == 0:
            self.session_manager.remove_session(connection.remote_address)

    def _on_data(self, connection: AX25Connection, data: bytes):
        """Handle incoming data from connection"""
        try:
            # Decode data as text
            message = data.decode('utf-8', errors='ignore').strip()

            if not message:
                return

            logger.info(f"Message from {connection.remote_address}: {message}")

            # Handle special commands
            if message.lower() in ['help', '?']:
                self._send_help(connection)
                return
            elif message.lower() in ['quit', 'bye', 'exit', '73']:
                self._send_to_station(connection, "73! Goodbye.\n")
                # Disconnect based on connection type
                if isinstance(connection, TelnetConnection):
                    self.telnet_server.disconnect(connection)
                else:
                    self.connection_handler.disconnect(connection)
                return
            elif message.lower() == 'status':
                self._send_status(connection)
                return
            elif message.lower() in ['clear', 'reset']:
                self.session_manager.clear_session(connection.remote_address)
                self._send_to_station(connection, "Conversation history cleared.\n")
                return

            # Check rate limits
            allowed, reason = self.rate_limiter.check_limit(connection.remote_address)
            if not allowed:
                self.activity_logger.log_rate_limit(connection.remote_address, reason)
                self._send_to_station(
                    connection,
                    f"Rate limit exceeded: {reason}\n"
                    "Please try again later. Type 'status' for details.\n"
                )
                return

            # Log query
            self.activity_logger.log_query(
                connection.remote_address,
                message,
                getattr(connection, 'connection_id', None)
            )

            # Get conversation history
            history = self.session_manager.get_history(connection.remote_address)

            # Send typing indicator
            self._send_to_station(connection, "...\n")

            # Query Claude
            start_time = time.time()
            response_text, tokens_used, error = self.claude_client.send_message(
                message,
                history
            )
            response_time_ms = int((time.time() - start_time) * 1000)

            if error:
                # Handle error
                self.activity_logger.log_error(
                    "ClaudeAPI",
                    error,
                    connection.remote_address
                )

                # Log to database
                self.database.log_query(
                    callsign=connection.remote_address,
                    query=message,
                    error=error,
                    connection_id=getattr(connection, 'connection_id', None)
                )

                self._send_to_station(
                    connection,
                    f"Error: {error}\nPlease try again.\n"
                )
                return

            # Update session history
            self.session_manager.add_user_message(connection.remote_address, message)
            self.session_manager.add_assistant_message(connection.remote_address, response_text)

            # Log response
            self.activity_logger.log_response(
                connection.remote_address,
                len(response_text),
                tokens_used,
                response_time_ms,
                getattr(connection, 'connection_id', None)
            )

            # Log to database
            self.database.log_query(
                callsign=connection.remote_address,
                query=message,
                response=response_text,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                connection_id=getattr(connection, 'connection_id', None)
            )

            # Truncate response if too long
            max_chars = self.config.max_response_chars
            if len(response_text) > max_chars:
                response_text = response_text[:max_chars]
                response_text += f"\n\n[Response truncated at {max_chars} chars]"

            # Send response
            self._send_to_station(connection, response_text + "\n")

        except Exception as e:
            logger.error(f"Error handling data: {e}", exc_info=True)
            self.activity_logger.log_error(
                "DataHandling",
                str(e),
                connection.remote_address,
                e
            )
            self._send_to_station(connection, "Internal error. Please try again.\n")

    def _send_to_station(self, connection, message: str):
        """Send message to connected station"""
        try:
            # Check connection type
            if isinstance(connection, TelnetConnection):
                # Telnet connection - send directly
                self.telnet_server.send_data(connection, message.encode('utf-8'))
            else:
                # AX.25 connection - split message into chunks if needed (max ~256 bytes per packet)
                chunk_size = 200
                for i in range(0, len(message), chunk_size):
                    chunk = message[i:i + chunk_size]
                    self.connection_handler.send_data(connection, chunk.encode('utf-8'))
                    time.sleep(0.1)  # Small delay between packets
        except Exception as e:
            logger.error(f"Error sending to station: {e}")

    def _send_help(self, connection: AX25Connection):
        """Send help message"""
        help_text = """
PacketClaude Help:
- Simply type your questions to chat with Claude AI
- 'help' or '?' - Show this help
- 'status' - Show rate limit status
- 'clear' - Clear conversation history
- 'quit', 'bye', or '73' - Disconnect

Your conversation context is preserved during the session.
"""
        self._send_to_station(connection, help_text)

    def _send_status(self, connection: AX25Connection):
        """Send status information"""
        status = self.rate_limiter.get_status(connection.remote_address)
        status_text = self.rate_limiter.format_limit_message(status)

        session = self.session_manager.get_session(connection.remote_address)
        status_text += f"\n\nSession: {len(session.messages)} messages in history"

        self._send_to_station(connection, status_text + "\n")

    @staticmethod
    def _parse_callsign(callsign_str: str) -> tuple:
        """Parse callsign string into callsign and SSID"""
        if '-' in callsign_str:
            parts = callsign_str.split('-')
            return parts[0].strip().upper(), int(parts[1])
        return callsign_str.strip().upper(), 0

    def stop(self):
        """Stop PacketClaude"""
        if not self.running:
            return

        logger.info("Stopping PacketClaude...")
        self.running = False

        self.activity_logger.log_shutdown()

        # Disconnect all connections
        if self.connection_handler:
            for conn in self.connection_handler.get_all_connections():
                self.connection_handler.disconnect(conn)

        # Disconnect all telnet connections
        if self.telnet_server:
            self.telnet_server.stop()

        # Disconnect from radio
        if self.radio_control:
            self.radio_control.disconnect()

        # Disconnect from KISS TNC
        if self.kiss_client:
            self.kiss_client.disconnect()

        logger.info("PacketClaude stopped")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='PacketClaude - AX.25 Packet Radio Gateway for Claude AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with both KISS and telnet (default)
  %(prog)s

  # Run telnet-only mode (no radio/Direwolf required)
  %(prog)s --telnet-only

  # Run KISS-only mode (no telnet)
  %(prog)s --kiss-only

  # Specify custom config file
  %(prog)s -c /path/to/config.yaml

  # Telnet-only on custom port
  %(prog)s --telnet-only --telnet-port 8888
        """
    )

    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file',
        default=None
    )

    # Interface mode options
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--telnet-only',
        action='store_true',
        help='Run in telnet-only mode (disable KISS/Direwolf connection)'
    )
    mode_group.add_argument(
        '--kiss-only',
        action='store_true',
        help='Run KISS-only mode (disable telnet server)'
    )

    # Override options
    parser.add_argument(
        '--telnet-port',
        type=int,
        help='Override telnet port from config'
    )
    parser.add_argument(
        '--telnet-host',
        help='Override telnet host from config'
    )
    parser.add_argument(
        '--direwolf-host',
        help='Override Direwolf host from config'
    )
    parser.add_argument(
        '--direwolf-port',
        type=int,
        help='Override Direwolf port from config'
    )

    args = parser.parse_args()

    # Validate environment
    if not _validate_environment():
        sys.exit(1)

    try:
        app = PacketClaude(
            config_path=args.config,
            telnet_only=args.telnet_only,
            kiss_only=args.kiss_only,
            telnet_port=args.telnet_port,
            telnet_host=args.telnet_host,
            direwolf_host=args.direwolf_host,
            direwolf_port=args.direwolf_port
        )
        app.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


def _validate_environment() -> bool:
    """
    Validate environment before starting

    Returns:
        True if environment is valid
    """
    from pathlib import Path
    import os

    # Check for config file
    config_path = os.getenv("CONFIG_PATH", "config/config.yaml")
    if not Path(config_path).exists():
        print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        print("Please copy config/config.yaml.example to config/config.yaml and configure it", file=sys.stderr)
        return False

    # Check for .env file
    if not Path(".env").exists():
        print("Warning: .env file not found", file=sys.stderr)
        print("Please copy .env.example to .env and add your Anthropic API key", file=sys.stderr)
        print("Or set ANTHROPIC_API_KEY environment variable", file=sys.stderr)
        # Don't fail here, let Config class handle it

    return True


if __name__ == '__main__':
    main()
