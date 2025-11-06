"""
File management tool for Claude
Allows Claude to help users with file operations
"""
import logging
import json
from typing import Dict, Any, Optional
from ..files.manager import FileManager


logger = logging.getLogger(__name__)


class FileTool:
    """
    Tool that allows Claude to help with file management
    """

    def __init__(self, file_manager: FileManager, enabled: bool = True):
        """
        Initialize file tool

        Args:
            file_manager: FileManager instance
            enabled: Whether tool is enabled
        """
        self.file_manager = file_manager
        self.enabled = enabled

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get Claude API tool definition

        Returns:
            Tool definition dictionary
        """
        return {
            "name": "file_management",
            "description": (
                "Manage files stored in PacketClaude. "
                "List available files, get file information, and help users with file operations. "
                "Files are transferred via YAPP protocol over AX.25. "
                "Use this when users ask about files, file transfers, uploads, or downloads."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "info", "help"],
                        "description": (
                            "Action to perform:\n"
                            "- list: List files accessible to the user\n"
                            "- info: Get information about a specific file\n"
                            "- help: Get help about file operations"
                        )
                    },
                    "file_id": {
                        "type": "integer",
                        "description": "File ID (required for 'info' action)"
                    },
                    "filter": {
                        "type": "string",
                        "enum": ["public", "private", "shared", "all"],
                        "description": "Filter files by access level (for 'list' action)"
                    },
                    "callsign": {
                        "type": "string",
                        "description": "User's callsign (extracted from connection context)"
                    }
                },
                "required": ["action", "callsign"]
            }
        }

    def execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """
        Execute tool call from Claude

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters

        Returns:
            JSON string with results
        """
        if tool_name != "file_management":
            return json.dumps({
                "error": f"Unknown tool: {tool_name}"
            })

        action = tool_input.get("action")
        callsign = tool_input.get("callsign", "")

        if not callsign:
            return json.dumps({
                "error": "Missing parameter",
                "message": "Callsign is required"
            })

        try:
            if action == "list":
                filter_val = tool_input.get("filter")
                result = self._list_files(callsign, filter_val)
            elif action == "info":
                file_id = tool_input.get("file_id")
                if file_id is None:
                    return json.dumps({
                        "error": "file_id is required for 'info' action"
                    })
                result = self._get_file_info(callsign, file_id)
            elif action == "help":
                result = self._get_help()
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}"
                })

            return json.dumps(result)

        except Exception as e:
            logger.error(f"Error executing file tool: {e}", exc_info=True)
            return json.dumps({
                "error": "File operation failed",
                "message": str(e)
            })

    def _list_files(self, callsign: str, filter: Optional[str]) -> Dict[str, Any]:
        """List files accessible to user"""
        access_filter = None if filter == "all" or not filter else filter

        files = self.file_manager.list_files(
            callsign=callsign,
            access_filter=access_filter
        )

        if not files:
            return {
                "success": True,
                "message": "No files found.",
                "files": []
            }

        # Format file list for Claude
        file_list = []
        for f in files:
            file_list.append({
                "id": f['id'],
                "filename": f['filename'],
                "size": self.file_manager.format_file_size(f['file_size']),
                "size_bytes": f['file_size'],
                "owner": f['owner_callsign'],
                "access": f['access_level'],
                "description": f['description'],
                "downloads": f['download_count'],
                "uploaded_at": f['uploaded_at']
            })

        return {
            "success": True,
            "message": f"Found {len(files)} file(s).",
            "files": file_list
        }

    def _get_file_info(self, callsign: str, file_id: int) -> Dict[str, Any]:
        """Get information about a file"""
        file_info, error = self.file_manager.get_file_info(file_id, callsign)

        if error:
            return {
                "success": False,
                "error": error
            }

        return {
            "success": True,
            "file": {
                "id": file_info['id'],
                "filename": file_info['filename'],
                "size": self.file_manager.format_file_size(file_info['file_size']),
                "size_bytes": file_info['file_size'],
                "mime_type": file_info['mime_type'],
                "owner": file_info['owner_callsign'],
                "access": file_info['access_level'],
                "description": file_info['description'],
                "uploaded_at": file_info['uploaded_at'],
                "download_count": file_info['download_count']
            }
        }

    def _get_help(self) -> Dict[str, Any]:
        """Get help about file operations"""
        help_text = """
File Transfer Commands:
- /upload - Start uploading a file via YAPP protocol
- /files [public|private|shared] - List available files
- /download <file_id> - Download a file by ID
- /fileinfo <file_id> - Get detailed information about a file
- /share <file_id> <callsign> - Share a file with another callsign
- /publicfile <file_id> - Make one of your files public
- /deletefile <file_id> - Delete one of your files

File Transfer Protocol:
- Files are transferred using YAPP (Yet Another Packet Protocol)
- YAPP is a standard amateur radio file transfer protocol
- Maximum file size: 100 KB
- Transfers work over AX.25 connections (not telnet)
- Use Packet Commander iOS app or other YAPP-capable software

File Access Levels:
- private: Only you can access the file
- public: Anyone can download the file
- shared: Specific callsigns you've shared with can access

Tips:
- You can ask me to list files, get file info, or help with operations
- I can't initiate uploads/downloads, but I can guide you through the process
- File IDs are shown when listing files - use these for download/share commands
"""
        return {
            "success": True,
            "help_text": help_text
        }
