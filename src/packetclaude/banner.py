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
    # Packet Claude ASCII art banner
    banner = r"""
 ____   _    ____ _  _______ _____    ____ _    _    _   _ ____  _____
|  _ \ / \  / ___| |/ / ____|_   _|  / ___| |  / \  | | | |  _ \| ____|
| |_) / _ \| |   | ' /|  _|   | |   | |   | | / _ \ | | | | | | |  _|
|  __/ ___ \ |___| . \| |___  | |   | |___| |/ ___ \| |_| | |_| | |___
|_| /_/   \_\____|_|\_\_____| |_|    \____|_/_/   \_\\___/|____/|_____|
"""

    # Add station info if provided
    if callsign or grid:
        station_info = []
        if callsign:
            station_info.append(callsign)
        if grid:
            station_info.append(grid)

        info_line = " • ".join(station_info)
        banner += f"\n  Packet Claude • {info_line}\n"
    else:
        banner += "\n  Packet Claude\n"

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
 ____   _    ____ _  _______ _____    ____ _    _    _   _ ____  _____
|  _ \ / \  / ___| |/ / ____|_   _|  / ___| |  / \  | | | |  _ \| ____|
| |_) / _ \| |   | ' /|  _|   | |   | |   | | / _ \ | | | | | | |  _|
|  __/ ___ \ |___| . \| |___  | |   | |___| |/ ___ \| |_| | |_| | |___
|_| /_/   \_\____|_|\_\_____| |_|    \____|_/_/   \_\\___/|____/|_____|
"""

    if callsign or grid:
        station_info = []
        if callsign:
            station_info.append(callsign)
        if grid:
            station_info.append(grid)
        info_line = " • ".join(station_info)
        banner += f"\n Packet Claude • {info_line}\n"
    else:
        banner += "\n Packet Claude\n"

    return banner
