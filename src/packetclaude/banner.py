"""
ASCII art banner for PacketClaude
"""


def get_banner(callsign: str = "", grid: str = "") -> str:
    """
    Get ASCII art banner with optional station info

    Args:
        callsign: Station callsign (e.g., "W2ASM-10")
        grid: Grid square (e.g., "FN30aq")

    Returns:
        ASCII art banner string
    """
    # Claude-inspired ASCII art
    banner = r"""
   _____ _                 _
  / ____| |               | |
 | |    | | __ _ _   _  __| | ___
 | |    | |/ _` | | | |/ _` |/ _ \
 | |____| | (_| | |_| | (_| |  __/
  \_____|_|\__,_|\__,_|\__,_|\___|
"""

    # Add station info if provided
    if callsign or grid:
        station_info = []
        if callsign:
            station_info.append(callsign)
        if grid:
            station_info.append(grid)

        info_line = " • ".join(station_info)
        banner += f"\n  PacketClaude • {info_line}\n"
    else:
        banner += "\n  PacketClaude\n"

    banner += "  AI-Powered Amateur Radio BBS\n"

    return banner


def get_compact_banner(callsign: str = "", grid: str = "") -> str:
    """
    Get a more compact ASCII art banner

    Args:
        callsign: Station callsign
        grid: Grid square

    Returns:
        Compact ASCII banner
    """
    banner = r"""
  _____ _                 _
 / ____| | __ _ _   _  __| | ___
| |    | |/ _` | | | |/ _` |/ _ \
| |____| | (_| | |_| | (_| |  __/
 \_____|_|\__,_|\__,_|\__,_|\___|
"""

    if callsign or grid:
        station_info = []
        if callsign:
            station_info.append(callsign)
        if grid:
            station_info.append(grid)
        info_line = " • ".join(station_info)
        banner += f"\n PacketClaude • {info_line}\n"
    else:
        banner += "\n PacketClaude\n"

    return banner
