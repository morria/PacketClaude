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
from .radio.hamlib_control import RadioControl, DummyRadioControl
from .claude.client import ClaudeClient
from .claude.session import SessionManager
from .auth.rate_limiter import RateLimiter
from .logging.activity_logger import setup_logging, ActivityLogger


logger = logging.getLogger(__name__)


class PacketClaude:
    """
    Main PacketClaude application
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize PacketClaude

        Args:
            config_path: Path to config file
        """
        # Load configuration
        self.config = Config(config_path)

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

        # Log startup configuration
        self.activity_logger.log_startup({
            'callsign': self.config.station_callsign,
            'direwolf_host': self.config.direwolf_host,
            'direwolf_port': self.config.direwolf_port,
            'radio_enabled': self.config.radio_enabled,
            'rate_limit_enabled': self.config.rate_limit_enabled,
        })

        # Initialize KISS client
        logger.info(f"Connecting to Direwolf at {self.config.direwolf_host}:{self.config.direwolf_port}")
        self.kiss_client = KISSClient(
            host=self.config.direwolf_host,
            port=self.config.direwolf_port,
            timeout=self.config.direwolf_timeout
        )

        if not self.kiss_client.connect():
            raise RuntimeError("Failed to connect to Direwolf KISS TNC")

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

        # Initialize radio control
        if self.config.radio_enabled:
            logger.info("Initializing radio control...")
            self.radio_control = RadioControl(
                model=self.config.radio_model,
                device=self.config.radio_device,
                baud=self.config.radio_baud,
                enabled=True
            )
            self.radio_control.connect()
        else:
            logger.info("Radio control disabled, using dummy control")
            self.radio_control = DummyRadioControl()

        # Initialize Claude client
        logger.info("Initializing Claude API client...")
        self.claude_client = ClaudeClient(
            api_key=self.config.anthropic_api_key,
            model=self.config.claude_model,
            max_tokens=self.config.claude_max_tokens,
            temperature=self.config.claude_temperature,
            system_prompt=self.config.claude_system_prompt
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
        logger.info(f"PacketClaude ready - listening as {self.config.station_callsign}")
        logger.info("Press Ctrl+C to stop")

        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        cleanup_thread.start()

        # Main receive loop
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

    def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.running:
            try:
                # Sleep for 60 seconds
                time.sleep(60)

                if not self.running:
                    break

                # Cleanup stale connections
                self.connection_handler.cleanup_stale_connections(
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

    def _send_to_station(self, connection: AX25Connection, message: str):
        """Send message to connected station"""
        try:
            # Split message into chunks if needed (max ~256 bytes per packet)
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

    parser = argparse.ArgumentParser(description='PacketClaude - AX.25 Packet Radio Gateway for Claude AI')
    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file',
        default=None
    )

    args = parser.parse_args()

    try:
        app = PacketClaude(config_path=args.config)
        app.start()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
