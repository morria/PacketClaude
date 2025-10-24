"""
Database management for PacketClaude
Handles activity logging and rate limiting tracking
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import contextmanager


class Database:
    """SQLite database manager for PacketClaude"""

    def __init__(self, db_path: Path):
        """
        Initialize database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Connection log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    callsign TEXT NOT NULL,
                    connected_at TIMESTAMP NOT NULL,
                    disconnected_at TIMESTAMP,
                    duration_seconds INTEGER,
                    packets_sent INTEGER DEFAULT 0,
                    packets_received INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Query log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    connection_id INTEGER,
                    callsign TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT,
                    tokens_used INTEGER,
                    response_time_ms INTEGER,
                    error TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (connection_id) REFERENCES connections(id)
                )
            """)

            # Rate limiting table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    callsign TEXT NOT NULL,
                    query_count INTEGER DEFAULT 1,
                    window_start TIMESTAMP NOT NULL,
                    window_end TIMESTAMP NOT NULL,
                    last_query TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Error log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    callsign TEXT,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    context TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_connections_callsign
                ON connections(callsign)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queries_callsign
                ON queries(callsign)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queries_timestamp
                ON queries(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rate_limits_callsign
                ON rate_limits(callsign)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_timestamp
                ON errors(timestamp)
            """)

    # Connection logging methods

    def log_connection(self, callsign: str) -> int:
        """
        Log a new connection

        Args:
            callsign: Station callsign

        Returns:
            Connection ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO connections (callsign, connected_at)
                VALUES (?, ?)
            """, (callsign, datetime.utcnow()))
            return cursor.lastrowid

    def log_disconnection(self, connection_id: int,
                         packets_sent: int = 0,
                         packets_received: int = 0):
        """
        Log a disconnection

        Args:
            connection_id: Connection ID
            packets_sent: Number of packets sent
            packets_received: Number of packets received
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get connection start time
            cursor.execute("""
                SELECT connected_at FROM connections WHERE id = ?
            """, (connection_id,))
            row = cursor.fetchone()

            if row:
                connected_at = datetime.fromisoformat(row['connected_at'])
                disconnected_at = datetime.utcnow()
                duration = int((disconnected_at - connected_at).total_seconds())

                cursor.execute("""
                    UPDATE connections
                    SET disconnected_at = ?,
                        duration_seconds = ?,
                        packets_sent = ?,
                        packets_received = ?
                    WHERE id = ?
                """, (disconnected_at, duration, packets_sent,
                      packets_received, connection_id))

    # Query logging methods

    def log_query(self, callsign: str, query: str,
                 response: str = None,
                 tokens_used: int = None,
                 response_time_ms: int = None,
                 error: str = None,
                 connection_id: int = None) -> int:
        """
        Log a query and response

        Args:
            callsign: Station callsign
            query: User query
            response: Claude response
            tokens_used: Number of tokens used
            response_time_ms: Response time in milliseconds
            error: Error message if query failed
            connection_id: Connection ID if available

        Returns:
            Query log ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO queries
                (connection_id, callsign, query, response, tokens_used,
                 response_time_ms, error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (connection_id, callsign, query, response, tokens_used,
                  response_time_ms, error))
            return cursor.lastrowid

    # Rate limiting methods

    def check_rate_limit(self, callsign: str,
                        queries_per_hour: int,
                        queries_per_day: int) -> tuple[bool, Optional[str]]:
        """
        Check if callsign is within rate limits

        Args:
            callsign: Station callsign
            queries_per_hour: Maximum queries per hour
            queries_per_day: Maximum queries per day

        Returns:
            Tuple of (allowed: bool, reason: str if not allowed)
        """
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check hourly limit
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM queries
                WHERE callsign = ? AND timestamp > ? AND error IS NULL
            """, (callsign, hour_ago))
            hourly_count = cursor.fetchone()['count']

            if hourly_count >= queries_per_hour:
                return False, f"Hourly limit reached ({queries_per_hour}/hour)"

            # Check daily limit
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM queries
                WHERE callsign = ? AND timestamp > ? AND error IS NULL
            """, (callsign, day_ago))
            daily_count = cursor.fetchone()['count']

            if daily_count >= queries_per_day:
                return False, f"Daily limit reached ({queries_per_day}/day)"

            return True, None

    def get_rate_limit_status(self, callsign: str,
                             queries_per_hour: int,
                             queries_per_day: int) -> Dict[str, Any]:
        """
        Get rate limit status for callsign

        Args:
            callsign: Station callsign
            queries_per_hour: Maximum queries per hour
            queries_per_day: Maximum queries per day

        Returns:
            Dictionary with rate limit status
        """
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get hourly count
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM queries
                WHERE callsign = ? AND timestamp > ? AND error IS NULL
            """, (callsign, hour_ago))
            hourly_count = cursor.fetchone()['count']

            # Get daily count
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM queries
                WHERE callsign = ? AND timestamp > ? AND error IS NULL
            """, (callsign, day_ago))
            daily_count = cursor.fetchone()['count']

            return {
                'hourly_used': hourly_count,
                'hourly_limit': queries_per_hour,
                'hourly_remaining': max(0, queries_per_hour - hourly_count),
                'daily_used': daily_count,
                'daily_limit': queries_per_day,
                'daily_remaining': max(0, queries_per_day - daily_count),
            }

    # Error logging methods

    def log_error(self, error_type: str, error_message: str,
                 callsign: str = None,
                 stack_trace: str = None,
                 context: Dict = None):
        """
        Log an error

        Args:
            error_type: Type of error
            error_message: Error message
            callsign: Station callsign if available
            stack_trace: Stack trace if available
            context: Additional context as dictionary
        """
        context_json = json.dumps(context) if context else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO errors
                (callsign, error_type, error_message, stack_trace, context)
                VALUES (?, ?, ?, ?, ?)
            """, (callsign, error_type, error_message, stack_trace, context_json))

    # Statistics and reporting methods

    def get_connection_stats(self, callsign: str = None) -> Dict[str, Any]:
        """
        Get connection statistics

        Args:
            callsign: Filter by callsign (optional)

        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            where_clause = "WHERE callsign = ?" if callsign else ""
            params = (callsign,) if callsign else ()

            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_connections,
                    AVG(duration_seconds) as avg_duration,
                    SUM(packets_sent) as total_packets_sent,
                    SUM(packets_received) as total_packets_received
                FROM connections
                {where_clause}
            """, params)

            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_query_stats(self, callsign: str = None,
                       since: datetime = None) -> Dict[str, Any]:
        """
        Get query statistics

        Args:
            callsign: Filter by callsign (optional)
            since: Filter by timestamp (optional)

        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            where_clauses = []
            params = []

            if callsign:
                where_clauses.append("callsign = ?")
                params.append(callsign)

            if since:
                where_clauses.append("timestamp > ?")
                params.append(since)

            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_queries,
                    COUNT(CASE WHEN error IS NULL THEN 1 END) as successful_queries,
                    COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as failed_queries,
                    AVG(tokens_used) as avg_tokens,
                    AVG(response_time_ms) as avg_response_time_ms
                FROM queries
                {where_clause}
            """, tuple(params))

            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_recent_queries(self, limit: int = 10,
                          callsign: str = None) -> List[Dict[str, Any]]:
        """
        Get recent queries

        Args:
            limit: Maximum number of queries to return
            callsign: Filter by callsign (optional)

        Returns:
            List of query dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            where_clause = "WHERE callsign = ?" if callsign else ""
            params = [callsign] if callsign else []
            params.append(limit)

            cursor.execute(f"""
                SELECT *
                FROM queries
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            """, tuple(params))

            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_data(self, days: int = 30):
        """
        Remove data older than specified days

        Args:
            days: Number of days to keep
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Clean old queries
            cursor.execute("""
                DELETE FROM queries WHERE timestamp < ?
            """, (cutoff,))

            # Clean old rate limit entries
            cursor.execute("""
                DELETE FROM rate_limits WHERE window_end < ?
            """, (cutoff,))

            # Clean old errors
            cursor.execute("""
                DELETE FROM errors WHERE timestamp < ?
            """, (cutoff,))
