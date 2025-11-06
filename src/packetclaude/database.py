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

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_callsign TEXT NOT NULL,
                    to_callsign TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    is_read INTEGER DEFAULT 0,
                    in_reply_to INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP,
                    deleted_at TIMESTAMP,
                    FOREIGN KEY (in_reply_to) REFERENCES messages(id)
                )
            """)

            # Files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_data BLOB NOT NULL,
                    file_size INTEGER NOT NULL,
                    mime_type TEXT,
                    checksum TEXT NOT NULL,
                    owner_callsign TEXT NOT NULL,
                    access_level TEXT NOT NULL DEFAULT 'private',
                    description TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    download_count INTEGER DEFAULT 0
                )
            """)

            # File shares table (for callsign-specific sharing)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_shares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    shared_with_callsign TEXT NOT NULL,
                    shared_by_callsign TEXT NOT NULL,
                    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
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
                CREATE INDEX IF NOT EXISTS idx_messages_to_callsign
                ON messages(to_callsign)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_from_callsign
                ON messages(from_callsign)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_created_at
                ON messages(created_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_timestamp
                ON errors(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_owner_callsign
                ON files(owner_callsign)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_access_level
                ON files(access_level)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_shares_file_id
                ON file_shares(file_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_shares_shared_with
                ON file_shares(shared_with_callsign)
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

    # Message methods

    def send_message(self, from_callsign: str, to_callsign: str,
                    subject: str, body: str, in_reply_to: Optional[int] = None) -> int:
        """
        Send a message to another user

        Args:
            from_callsign: Sender's callsign
            to_callsign: Recipient's callsign
            subject: Message subject
            body: Message body
            in_reply_to: Optional message ID this is replying to

        Returns:
            Message ID of the sent message
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (from_callsign, to_callsign, subject, body, in_reply_to)
                VALUES (?, ?, ?, ?, ?)
            """, (from_callsign.upper(), to_callsign.upper(), subject, body, in_reply_to))
            return cursor.lastrowid

    def get_messages(self, callsign: str, unread_only: bool = False,
                    include_deleted: bool = False) -> List[Dict]:
        """
        Get messages for a callsign (received messages)

        Args:
            callsign: Callsign to get messages for
            unread_only: Only return unread messages
            include_deleted: Include deleted messages

        Returns:
            List of message dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, from_callsign, to_callsign, subject, body,
                       is_read, in_reply_to, created_at, read_at, deleted_at
                FROM messages
                WHERE to_callsign = ?
            """
            params = [callsign.upper()]

            if not include_deleted:
                query += " AND deleted_at IS NULL"

            if unread_only:
                query += " AND is_read = 0"

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row['id'],
                    'from': row['from_callsign'],
                    'to': row['to_callsign'],
                    'subject': row['subject'],
                    'body': row['body'],
                    'is_read': bool(row['is_read']),
                    'in_reply_to': row['in_reply_to'],
                    'created_at': row['created_at'],
                    'read_at': row['read_at'],
                    'deleted_at': row['deleted_at']
                })

            return messages

    def get_sent_messages(self, callsign: str) -> List[Dict]:
        """
        Get messages sent by a callsign

        Args:
            callsign: Callsign to get sent messages for

        Returns:
            List of message dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, from_callsign, to_callsign, subject, body,
                       is_read, in_reply_to, created_at, read_at, deleted_at
                FROM messages
                WHERE from_callsign = ? AND deleted_at IS NULL
                ORDER BY created_at DESC
            """

            cursor.execute(query, [callsign.upper()])

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row['id'],
                    'from': row['from_callsign'],
                    'to': row['to_callsign'],
                    'subject': row['subject'],
                    'body': row['body'],
                    'is_read': bool(row['is_read']),
                    'in_reply_to': row['in_reply_to'],
                    'created_at': row['created_at'],
                    'read_at': row['read_at'],
                    'deleted_at': row['deleted_at']
                })

            return messages

    def get_message(self, message_id: int, callsign: str) -> Optional[Dict]:
        """
        Get a specific message

        Args:
            message_id: Message ID
            callsign: Callsign (must be sender or recipient)

        Returns:
            Message dictionary or None if not found or not authorized
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, from_callsign, to_callsign, subject, body,
                       is_read, in_reply_to, created_at, read_at, deleted_at
                FROM messages
                WHERE id = ? AND (from_callsign = ? OR to_callsign = ?)
            """, (message_id, callsign.upper(), callsign.upper()))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'id': row['id'],
                'from': row['from_callsign'],
                'to': row['to_callsign'],
                'subject': row['subject'],
                'body': row['body'],
                'is_read': bool(row['is_read']),
                'in_reply_to': row['in_reply_to'],
                'created_at': row['created_at'],
                'read_at': row['read_at'],
                'deleted_at': row['deleted_at']
            }

    def mark_message_read(self, message_id: int, callsign: str) -> bool:
        """
        Mark a message as read

        Args:
            message_id: Message ID
            callsign: Callsign (must be recipient)

        Returns:
            True if message was marked read, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE messages
                SET is_read = 1, read_at = CURRENT_TIMESTAMP
                WHERE id = ? AND to_callsign = ? AND is_read = 0
            """, (message_id, callsign.upper()))
            return cursor.rowcount > 0

    def delete_message(self, message_id: int, callsign: str) -> bool:
        """
        Delete a message (soft delete)

        Args:
            message_id: Message ID
            callsign: Callsign (must be recipient)

        Returns:
            True if message was deleted, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE messages
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = ? AND to_callsign = ? AND deleted_at IS NULL
            """, (message_id, callsign.upper()))
            return cursor.rowcount > 0

    def get_unread_count(self, callsign: str) -> int:
        """
        Get count of unread messages for a callsign

        Args:
            callsign: Callsign

        Returns:
            Number of unread messages
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM messages
                WHERE to_callsign = ? AND is_read = 0 AND deleted_at IS NULL
            """, (callsign.upper(),))
            row = cursor.fetchone()
            return row['count'] if row else 0

    # File management methods

    def save_file(self, filename: str, file_data: bytes, file_size: int,
                  mime_type: str, checksum: str, owner_callsign: str,
                  access_level: str = 'private', description: str = None) -> int:
        """
        Save a file to the database

        Args:
            filename: Original filename
            file_data: File contents as bytes
            file_size: File size in bytes
            mime_type: MIME type of the file
            checksum: MD5 checksum of file data
            owner_callsign: Callsign of file owner
            access_level: Access level ('private', 'public', 'shared')
            description: Optional file description

        Returns:
            File ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO files (filename, file_data, file_size, mime_type,
                                 checksum, owner_callsign, access_level, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (filename, file_data, file_size, mime_type, checksum,
                  owner_callsign.upper(), access_level, description))
            return cursor.lastrowid

    def get_file(self, file_id: int) -> Optional[Dict]:
        """
        Get a file by ID

        Args:
            file_id: File ID

        Returns:
            File dictionary or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_data, file_size, mime_type,
                       checksum, owner_callsign, access_level, description,
                       uploaded_at, download_count
                FROM files
                WHERE id = ?
            """, (file_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'id': row['id'],
                'filename': row['filename'],
                'file_data': row['file_data'],
                'file_size': row['file_size'],
                'mime_type': row['mime_type'],
                'checksum': row['checksum'],
                'owner_callsign': row['owner_callsign'],
                'access_level': row['access_level'],
                'description': row['description'],
                'uploaded_at': row['uploaded_at'],
                'download_count': row['download_count']
            }

    def list_files(self, callsign: str = None, access_filter: str = None,
                   include_data: bool = False) -> List[Dict]:
        """
        List files accessible to a callsign

        Args:
            callsign: Callsign to check access for (if None, only public files)
            access_filter: Filter by access level ('public', 'private', 'shared')
            include_data: Include file_data in results (default False for listings)

        Returns:
            List of file dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build query
            fields = ['id', 'filename', 'file_size', 'mime_type', 'checksum',
                     'owner_callsign', 'access_level', 'description',
                     'uploaded_at', 'download_count']
            if include_data:
                fields.insert(2, 'file_data')

            query = f"SELECT {', '.join(fields)} FROM files WHERE 1=1"
            params = []

            # Filter by access
            if callsign:
                callsign_upper = callsign.upper()
                # User can see: their own files, public files, and files shared with them
                query += """ AND (
                    owner_callsign = ?
                    OR access_level = 'public'
                    OR (access_level = 'shared' AND id IN (
                        SELECT file_id FROM file_shares WHERE shared_with_callsign = ?
                    ))
                )"""
                params.extend([callsign_upper, callsign_upper])
            else:
                # No callsign - only public files
                query += " AND access_level = 'public'"

            # Apply access filter
            if access_filter:
                query += " AND access_level = ?"
                params.append(access_filter)

            query += " ORDER BY uploaded_at DESC"

            cursor.execute(query, params)

            files = []
            for row in cursor.fetchall():
                file_dict = {
                    'id': row['id'],
                    'filename': row['filename'],
                    'file_size': row['file_size'],
                    'mime_type': row['mime_type'],
                    'checksum': row['checksum'],
                    'owner_callsign': row['owner_callsign'],
                    'access_level': row['access_level'],
                    'description': row['description'],
                    'uploaded_at': row['uploaded_at'],
                    'download_count': row['download_count']
                }
                if include_data:
                    file_dict['file_data'] = row['file_data']
                files.append(file_dict)

            return files

    def delete_file(self, file_id: int, callsign: str) -> bool:
        """
        Delete a file (only owner can delete)

        Args:
            file_id: File ID
            callsign: Callsign attempting to delete

        Returns:
            True if deleted, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM files
                WHERE id = ? AND owner_callsign = ?
            """, (file_id, callsign.upper()))
            return cursor.rowcount > 0

    def share_file(self, file_id: int, owner_callsign: str,
                  shared_with_callsign: str) -> bool:
        """
        Share a file with a specific callsign

        Args:
            file_id: File ID
            owner_callsign: File owner's callsign
            shared_with_callsign: Callsign to share with

        Returns:
            True if shared successfully
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership
            cursor.execute("""
                SELECT id, access_level FROM files
                WHERE id = ? AND owner_callsign = ?
            """, (file_id, owner_callsign.upper()))
            file_row = cursor.fetchone()

            if not file_row:
                return False

            # Update access level to 'shared' if it's not already
            if file_row['access_level'] != 'shared':
                cursor.execute("""
                    UPDATE files SET access_level = 'shared'
                    WHERE id = ?
                """, (file_id,))

            # Add share entry (check for duplicates)
            cursor.execute("""
                INSERT OR IGNORE INTO file_shares
                (file_id, shared_with_callsign, shared_by_callsign)
                VALUES (?, ?, ?)
            """, (file_id, shared_with_callsign.upper(), owner_callsign.upper()))

            return True

    def check_file_access(self, file_id: int, callsign: str) -> bool:
        """
        Check if a callsign has access to a file

        Args:
            file_id: File ID
            callsign: Callsign to check

        Returns:
            True if access allowed
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get file info
            cursor.execute("""
                SELECT owner_callsign, access_level FROM files WHERE id = ?
            """, (file_id,))
            row = cursor.fetchone()

            if not row:
                return False

            callsign_upper = callsign.upper()

            # Owner always has access
            if row['owner_callsign'] == callsign_upper:
                return True

            # Public files are accessible to all
            if row['access_level'] == 'public':
                return True

            # Check if file is shared with this callsign
            if row['access_level'] == 'shared':
                cursor.execute("""
                    SELECT id FROM file_shares
                    WHERE file_id = ? AND shared_with_callsign = ?
                """, (file_id, callsign_upper))
                return cursor.fetchone() is not None

            return False

    def increment_download_count(self, file_id: int):
        """
        Increment the download count for a file

        Args:
            file_id: File ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE files SET download_count = download_count + 1
                WHERE id = ?
            """, (file_id,))

    def get_file_count(self, callsign: str) -> int:
        """
        Get count of files owned by a callsign

        Args:
            callsign: Callsign

        Returns:
            Number of files
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM files WHERE owner_callsign = ?
            """, (callsign.upper(),))
            row = cursor.fetchone()
            return row['count'] if row else 0

    def get_total_file_size(self, callsign: str) -> int:
        """
        Get total size of files owned by a callsign

        Args:
            callsign: Callsign

        Returns:
            Total file size in bytes
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(file_size) as total FROM files WHERE owner_callsign = ?
            """, (callsign.upper(),))
            row = cursor.fetchone()
            return row['total'] if row and row['total'] else 0
