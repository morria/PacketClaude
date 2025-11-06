"""
File manager for PacketClaude
Handles file upload, download, storage, and access control
"""
import hashlib
import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from ..database import Database


logger = logging.getLogger(__name__)


class FileManager:
    """
    Manages file operations for PacketClaude
    """

    # File size limits
    MAX_FILE_SIZE = 100 * 1024  # 100 KB default
    MAX_FILES_PER_USER = 50  # Maximum files per user
    MAX_TOTAL_SIZE_PER_USER = 5 * 1024 * 1024  # 5 MB total per user

    # Allowed filename characters
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')

    def __init__(self, database: Database, max_file_size: int = None):
        """
        Initialize file manager

        Args:
            database: Database instance
            max_file_size: Maximum file size in bytes (optional)
        """
        self.database = database

        if max_file_size:
            self.MAX_FILE_SIZE = max_file_size

        logger.info(f"FileManager initialized with max size: {self.MAX_FILE_SIZE} bytes")

    def validate_filename(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate filename

        Args:
            filename: Filename to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "Filename cannot be empty"

        if len(filename) > 128:
            return False, "Filename too long (max 128 characters)"

        # Check for valid characters
        if not self.FILENAME_PATTERN.match(filename):
            return False, "Filename contains invalid characters (use only a-z, A-Z, 0-9, ., _, -)"

        # Check for directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "Filename cannot contain path separators"

        return True, None

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = os.path.basename(filename)

        # Replace invalid characters with underscore
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Limit length
        if len(filename) > 128:
            # Preserve extension if possible
            name, ext = os.path.splitext(filename)
            filename = name[:128-len(ext)] + ext

        return filename

    def calculate_checksum(self, data: bytes) -> str:
        """
        Calculate MD5 checksum of file data

        Args:
            data: File data

        Returns:
            Hex string of MD5 checksum
        """
        return hashlib.md5(data).hexdigest()

    def guess_mime_type(self, filename: str) -> str:
        """
        Guess MIME type from filename

        Args:
            filename: Filename

        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'

    def check_quota(self, callsign: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user has quota for uploading file

        Args:
            callsign: User's callsign
            file_size: Size of file to upload

        Returns:
            Tuple of (allowed, error_message)
        """
        # Check file size limit
        if file_size > self.MAX_FILE_SIZE:
            return False, f"File too large (max {self.MAX_FILE_SIZE} bytes)"

        # Check file count
        file_count = self.database.get_file_count(callsign)
        if file_count >= self.MAX_FILES_PER_USER:
            return False, f"Maximum file count reached ({self.MAX_FILES_PER_USER} files)"

        # Check total size
        total_size = self.database.get_total_file_size(callsign)
        if total_size + file_size > self.MAX_TOTAL_SIZE_PER_USER:
            return False, f"Storage quota exceeded (max {self.MAX_TOTAL_SIZE_PER_USER} bytes)"

        return True, None

    def upload_file(self, filename: str, file_data: bytes, owner_callsign: str,
                   access_level: str = 'private', description: str = None) -> Tuple[Optional[int], Optional[str]]:
        """
        Upload a file

        Args:
            filename: Original filename
            file_data: File contents
            owner_callsign: Owner's callsign
            access_level: Access level ('private', 'public', 'shared')
            description: Optional file description

        Returns:
            Tuple of (file_id, error_message)
        """
        # Sanitize filename
        filename = self.sanitize_filename(filename)

        # Validate filename
        valid, error = self.validate_filename(filename)
        if not valid:
            logger.warning(f"Invalid filename from {owner_callsign}: {filename} - {error}")
            return None, error

        # Check quota
        allowed, error = self.check_quota(owner_callsign, len(file_data))
        if not allowed:
            logger.warning(f"Quota exceeded for {owner_callsign}: {error}")
            return None, error

        # Calculate checksum
        checksum = self.calculate_checksum(file_data)

        # Guess MIME type
        mime_type = self.guess_mime_type(filename)

        # Validate access level
        if access_level not in ['private', 'public', 'shared']:
            access_level = 'private'

        try:
            # Save to database
            file_id = self.database.save_file(
                filename=filename,
                file_data=file_data,
                file_size=len(file_data),
                mime_type=mime_type,
                checksum=checksum,
                owner_callsign=owner_callsign,
                access_level=access_level,
                description=description
            )

            logger.info(f"File uploaded: {filename} (ID: {file_id}) by {owner_callsign}, "
                       f"{len(file_data)} bytes, {access_level}")

            return file_id, None

        except Exception as e:
            logger.error(f"Failed to upload file: {e}", exc_info=True)
            return None, f"Upload failed: {str(e)}"

    def download_file(self, file_id: int, callsign: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Download a file

        Args:
            file_id: File ID
            callsign: Requesting callsign

        Returns:
            Tuple of (file_dict, error_message)
        """
        # Check access
        if not self.database.check_file_access(file_id, callsign):
            logger.warning(f"Access denied: {callsign} attempted to download file {file_id}")
            return None, "Access denied"

        # Get file
        file_dict = self.database.get_file(file_id)
        if not file_dict:
            return None, "File not found"

        # Verify checksum
        calculated_checksum = self.calculate_checksum(file_dict['file_data'])
        if calculated_checksum != file_dict['checksum']:
            logger.error(f"Checksum mismatch for file {file_id}")
            return None, "File integrity check failed"

        # Increment download count
        self.database.increment_download_count(file_id)

        logger.info(f"File downloaded: {file_dict['filename']} (ID: {file_id}) by {callsign}")

        return file_dict, None

    def list_files(self, callsign: str, access_filter: str = None) -> List[Dict]:
        """
        List files accessible to a callsign

        Args:
            callsign: Callsign
            access_filter: Filter by access level (optional)

        Returns:
            List of file metadata dictionaries (without file_data)
        """
        return self.database.list_files(
            callsign=callsign,
            access_filter=access_filter,
            include_data=False
        )

    def get_file_info(self, file_id: int, callsign: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get file information (metadata only, no data)

        Args:
            file_id: File ID
            callsign: Requesting callsign

        Returns:
            Tuple of (file_info_dict, error_message)
        """
        # Check access
        if not self.database.check_file_access(file_id, callsign):
            return None, "Access denied"

        # Get file (without data in the listing)
        files = self.database.list_files(callsign=callsign, include_data=False)
        file_info = next((f for f in files if f['id'] == file_id), None)

        if not file_info:
            return None, "File not found"

        return file_info, None

    def delete_file(self, file_id: int, callsign: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file

        Args:
            file_id: File ID
            callsign: Owner's callsign

        Returns:
            Tuple of (success, error_message)
        """
        success = self.database.delete_file(file_id, callsign)

        if success:
            logger.info(f"File deleted: ID {file_id} by {callsign}")
            return True, None
        else:
            logger.warning(f"Delete failed: ID {file_id} by {callsign} (not owner or not found)")
            return False, "Delete failed (not owner or file not found)"

    def share_file(self, file_id: int, owner_callsign: str,
                  shared_with_callsign: str) -> Tuple[bool, Optional[str]]:
        """
        Share a file with another callsign

        Args:
            file_id: File ID
            owner_callsign: Owner's callsign
            shared_with_callsign: Callsign to share with

        Returns:
            Tuple of (success, error_message)
        """
        # Validate callsign format (basic check)
        if not shared_with_callsign or len(shared_with_callsign) > 10:
            return False, "Invalid callsign"

        success = self.database.share_file(file_id, owner_callsign, shared_with_callsign)

        if success:
            logger.info(f"File shared: ID {file_id} from {owner_callsign} to {shared_with_callsign}")
            return True, None
        else:
            logger.warning(f"Share failed: ID {file_id} by {owner_callsign}")
            return False, "Share failed (not owner or file not found)"

    def set_file_public(self, file_id: int, owner_callsign: str) -> Tuple[bool, Optional[str]]:
        """
        Make a file public

        Args:
            file_id: File ID
            owner_callsign: Owner's callsign

        Returns:
            Tuple of (success, error_message)
        """
        # Get file and verify ownership
        file_dict = self.database.get_file(file_id)
        if not file_dict:
            return False, "File not found"

        if file_dict['owner_callsign'] != owner_callsign.upper():
            return False, "Not file owner"

        # Update access level in database
        # We need to add an update method - for now, delete and re-upload won't work
        # Let's use a direct SQL update via the database connection
        try:
            with self.database._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE files SET access_level = 'public'
                    WHERE id = ? AND owner_callsign = ?
                """, (file_id, owner_callsign.upper()))

                if cursor.rowcount > 0:
                    logger.info(f"File set to public: ID {file_id} by {owner_callsign}")
                    return True, None
                else:
                    return False, "Update failed"

        except Exception as e:
            logger.error(f"Failed to set file public: {e}")
            return False, f"Update failed: {str(e)}"

    def format_file_size(self, size_bytes: int) -> str:
        """
        Format file size for human reading

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 KB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def format_file_list(self, files: List[Dict], show_owner: bool = True) -> str:
        """
        Format file list for display

        Args:
            files: List of file dictionaries
            show_owner: Include owner in display

        Returns:
            Formatted string
        """
        if not files:
            return "No files found."

        lines = []
        lines.append("ID  | Filename                     | Size    | Owner      | Access")
        lines.append("----|------------------------------|---------|------------|--------")

        for f in files:
            filename = f['filename'][:28].ljust(28)
            size_str = self.format_file_size(f['file_size']).rjust(7)
            owner = f['owner_callsign'][:10].ljust(10) if show_owner else ""
            access = f['access_level'][:7]

            if show_owner:
                line = f"{f['id']:<4}| {filename} | {size_str} | {owner} | {access}"
            else:
                line = f"{f['id']:<4}| {filename} | {size_str} | {access}"

            lines.append(line)

        return '\n'.join(lines)
