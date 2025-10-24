#!/usr/bin/env python3
"""
PacketClaude Launcher
Convenience wrapper for running PacketClaude
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Run main
from packetclaude.main import main

if __name__ == '__main__':
    main()
