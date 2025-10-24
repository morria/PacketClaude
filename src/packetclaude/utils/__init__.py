"""
Utility functions for PacketClaude
"""

def normalize_callsign(callsign: str) -> str:
    """
    Normalize a callsign to base form (remove SSID and prefixes/suffixes)

    Examples:
        W2ASM-2 -> W2ASM
        VE2/W2ASM/3 -> W2ASM
        w2asm -> W2ASM

    Args:
        callsign: Raw callsign string

    Returns:
        Normalized callsign (uppercase, no SSID, no prefix/suffix)
    """
    if not callsign:
        return ""

    # Convert to uppercase
    callsign = callsign.upper().strip()

    # Remove SSID (everything after last hyphen)
    if '-' in callsign:
        callsign = callsign.rsplit('-', 1)[0]

    # Remove prefix/suffix (take middle part if slashes present)
    if '/' in callsign:
        parts = callsign.split('/')
        # Find the part that looks most like a base callsign
        # Usually the one without numbers at the start or end only
        for part in parts:
            if part and part[0].isalpha() and any(c.isdigit() for c in part):
                callsign = part
                break

    return callsign


__all__ = ['normalize_callsign']
