#!/usr/bin/env python3
"""
Upload README.txt to PacketClaude file system as a public file
Run this script to make the README available to all BBS users
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from packetclaude.database import Database
from packetclaude.files.manager import FileManager
from packetclaude.config import Config


def main():
    """Upload README.txt as a public system file"""

    # Initialize config and database
    config = Config()
    database = Database(config.database_path)
    file_manager = FileManager(database, max_file_size=config.file_transfer_max_size)

    # Read README.txt
    readme_path = Path(__file__).parent.parent / "src" / "packetclaude" / "files" / "README.txt"

    if not readme_path.exists():
        print(f"ERROR: README.txt not found at {readme_path}")
        return 1

    print(f"Reading README.txt from {readme_path}")
    with open(readme_path, 'rb') as f:
        readme_data = f.read()

    print(f"File size: {len(readme_data)} bytes")

    # Upload as system file (owned by SYSOP)
    file_id, error = file_manager.upload_file(
        filename="README.txt",
        file_data=readme_data,
        owner_callsign="SYSOP",
        access_level="public",
        description="PacketClaude BBS Instructions and Command Reference"
    )

    if error:
        print(f"ERROR uploading file: {error}")
        return 1

    print(f"\n✓ README.txt uploaded successfully!")
    print(f"  File ID: {file_id}")
    print(f"  Filename: README.txt")
    print(f"  Size: {len(readme_data)} bytes")
    print(f"  Access: public")
    print(f"  Owner: SYSOP")
    print(f"\nAll BBS users can now download it with: /download {file_id}")
    print(f"Or list files with: /files public")

    return 0


if __name__ == "__main__":
    sys.exit(main())
