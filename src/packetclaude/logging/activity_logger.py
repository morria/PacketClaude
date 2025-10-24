"""
Activity logging for PacketClaude
Logs all connections, queries, and system events
"""
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(log_dir: Path,
                 log_level: str = "INFO",
                 log_format: str = "json",
                 console_output: bool = True) -> logging.Logger:
    """
    Setup logging configuration

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Log format ('json' or 'text')
        console_output: Also output to console

    Returns:
        Configured logger
    """
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # File handler for main log
    log_file = log_dir / f"packetclaude_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

    # Format
    if log_format == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console_output:
        # Use text format for console for readability
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info("Logging initialized")
    return logger


class JsonFormatter(logging.Formatter):
    """
    JSON log formatter
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'callsign'):
            log_data['callsign'] = record.callsign
        if hasattr(record, 'connection_id'):
            log_data['connection_id'] = record.connection_id

        return json.dumps(log_data)


class ActivityLogger:
    """
    High-level activity logger for PacketClaude events
    """

    def __init__(self, logger: logging.Logger, database=None):
        """
        Initialize activity logger

        Args:
            logger: Logging instance
            database: Database instance for persistent logging
        """
        self.logger = logger
        self.database = database

    def log_connection(self, callsign: str, connection_id: Optional[int] = None):
        """Log a new connection"""
        self.logger.info(
            f"Connection from {callsign}",
            extra={'callsign': callsign, 'connection_id': connection_id}
        )

    def log_disconnection(self, callsign: str,
                         connection_id: Optional[int] = None,
                         duration: Optional[float] = None):
        """Log a disconnection"""
        msg = f"Disconnection from {callsign}"
        if duration:
            msg += f" (duration: {duration:.1f}s)"

        self.logger.info(
            msg,
            extra={'callsign': callsign, 'connection_id': connection_id}
        )

    def log_query(self, callsign: str, query: str,
                 connection_id: Optional[int] = None):
        """Log a user query"""
        # Truncate long queries for logging
        query_preview = query[:100] + "..." if len(query) > 100 else query

        self.logger.info(
            f"Query from {callsign}: {query_preview}",
            extra={'callsign': callsign, 'connection_id': connection_id}
        )

    def log_response(self, callsign: str,
                    response_length: int,
                    tokens_used: Optional[int] = None,
                    response_time_ms: Optional[int] = None,
                    connection_id: Optional[int] = None):
        """Log a Claude response"""
        msg = f"Response to {callsign}: {response_length} chars"
        if tokens_used:
            msg += f", {tokens_used} tokens"
        if response_time_ms:
            msg += f", {response_time_ms}ms"

        self.logger.info(
            msg,
            extra={'callsign': callsign, 'connection_id': connection_id}
        )

    def log_rate_limit(self, callsign: str, reason: str):
        """Log rate limit event"""
        self.logger.warning(
            f"Rate limit for {callsign}: {reason}",
            extra={'callsign': callsign}
        )

    def log_error(self, error_type: str, error_message: str,
                 callsign: Optional[str] = None,
                 exception: Optional[Exception] = None):
        """Log an error"""
        self.logger.error(
            f"{error_type}: {error_message}",
            extra={'callsign': callsign},
            exc_info=exception
        )

        # Also log to database if available
        if self.database:
            stack_trace = None
            if exception:
                import traceback
                stack_trace = ''.join(traceback.format_tb(exception.__traceback__))

            self.database.log_error(
                error_type=error_type,
                error_message=error_message,
                callsign=callsign,
                stack_trace=stack_trace
            )

    def log_startup(self, config: dict):
        """Log system startup"""
        self.logger.info("PacketClaude starting up")
        self.logger.info(f"Station callsign: {config.get('callsign', 'UNKNOWN')}")
        self.logger.info(f"Direwolf: {config.get('direwolf_host')}:{config.get('direwolf_port')}")
        self.logger.info(f"Radio control: {'enabled' if config.get('radio_enabled') else 'disabled'}")
        self.logger.info(f"Rate limiting: {'enabled' if config.get('rate_limit_enabled') else 'disabled'}")

    def log_shutdown(self, reason: Optional[str] = None):
        """Log system shutdown"""
        msg = "PacketClaude shutting down"
        if reason:
            msg += f": {reason}"
        self.logger.info(msg)

    def log_stats(self, stats: dict):
        """Log statistics"""
        self.logger.info(f"Statistics: {json.dumps(stats)}")
