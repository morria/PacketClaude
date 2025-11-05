"""
DX Cluster spots tool for Claude
Fetches current DX spots from HamQTH DX Cluster API with filtering by band and mode
"""
import logging
import json
import time
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import requests


logger = logging.getLogger(__name__)


class DXClusterTool:
    """
    DX Cluster tool for fetching DX spots with filtering
    Uses HamQTH DX Cluster API (hamqth.com)
    """

    # HamQTH DX Cluster API endpoint
    API_URL = "https://www.hamqth.com/dxc_csv.php"

    # Band definitions (frequency ranges in kHz)
    BANDS = {
        "160m": (1800, 2000),
        "80m": (3500, 4000),
        "60m": (5300, 5405),
        "40m": (7000, 7300),
        "30m": (10100, 10150),
        "20m": (14000, 14350),
        "17m": (18068, 18168),
        "15m": (21000, 21450),
        "12m": (24890, 24990),
        "10m": (28000, 29700),
        "6m": (50000, 54000),
        "2m": (144000, 148000),
        "70cm": (420000, 450000),
    }

    # Common mode aliases
    MODE_ALIASES = {
        "ssb": ["SSB", "USB", "LSB", "PHONE"],
        "cw": ["CW", "CWL", "CWU"],
        "digital": ["FT8", "FT4", "RTTY", "PSK31", "PSK", "JT65", "MFSK", "OLIVIA", "THOR"],
        "ft8": ["FT8"],
        "ft4": ["FT4"],
        "rtty": ["RTTY"],
        "psk": ["PSK31", "PSK"],
        "phone": ["SSB", "USB", "LSB", "PHONE", "AM", "FM"],
    }

    def __init__(self, enabled: bool = True, max_spots: int = 15):
        """
        Initialize DX Cluster tool

        Args:
            enabled: Enable/disable DX Cluster functionality
            max_spots: Maximum number of spots to return (default: 15)
        """
        self.enabled = enabled
        self.max_spots = max_spots
        self._cache = None
        self._cache_time = 0
        self._cache_duration = 15  # Cache for 15 seconds (HamQTH updates every 15 seconds)

    def _freq_to_band(self, freq_khz: float) -> Optional[str]:
        """
        Convert frequency in kHz to band name

        Args:
            freq_khz: Frequency in kHz

        Returns:
            Band name (e.g., "20m") or None if not in ham bands
        """
        for band, (low, high) in self.BANDS.items():
            if low <= freq_khz <= high:
                return band

        return None

    def _band_to_adif(self, band: str) -> Optional[str]:
        """
        Convert band name to ADIF format for HamQTH API

        Args:
            band: Band in format like "20m", "40m"

        Returns:
            ADIF band format like "20M", "40M"
        """
        if not band:
            return None
        return band.upper()

    def _normalize_mode(self, mode: str) -> str:
        """
        Normalize mode string for comparison

        Args:
            mode: Mode string from API

        Returns:
            Normalized mode string
        """
        if not mode:
            return ""
        return mode.upper().strip()

    def _mode_matches(self, spot_mode: str, filter_mode: str) -> bool:
        """
        Check if spot mode matches filter mode (with aliases)

        Args:
            spot_mode: Mode from the spot
            filter_mode: User's filter mode

        Returns:
            True if modes match
        """
        spot_mode = self._normalize_mode(spot_mode)
        filter_mode_lower = filter_mode.lower()

        # Check direct match
        if spot_mode == filter_mode.upper():
            return True

        # Check aliases
        if filter_mode_lower in self.MODE_ALIASES:
            return spot_mode in self.MODE_ALIASES[filter_mode_lower]

        return False

    def get_spots(self, band: Optional[str] = None, mode: Optional[str] = None,
                  minutes: int = 30, count: Optional[int] = None) -> str:
        """
        Fetch DX spots from API with filtering

        Args:
            band: Band to filter (e.g., "20m"), None for all bands
            mode: Mode to filter (e.g., "CW", "SSB"), None for all modes
            minutes: How many minutes back to look for spots
            count: Maximum number of spots to return (overrides max_spots)

        Returns:
            JSON string with filtered spots
        """
        if not self.enabled:
            return json.dumps({
                "error": "DX Cluster tool is disabled"
            })

        try:
            logger.info(f"Fetching DX spots (band={band}, mode={mode}, minutes={minutes})")

            # Build API request parameters
            params = {
                "limit": "200"  # Get maximum spots
            }

            # Add band filter if specified (HamQTH uses ADIF format)
            if band:
                adif_band = self._band_to_adif(band)
                if adif_band:
                    params["band"] = adif_band

            # Use cache if available and fresh (for same params)
            current_time = time.time()
            cache_key = f"{band}_{mode}"
            if (self._cache and
                self._cache.get("key") == cache_key and
                (current_time - self._cache_time) < self._cache_duration):
                logger.debug("Using cached DX spots")
                csv_lines = self._cache["data"]
            else:
                # Fetch spots from API
                logger.debug(f"Requesting HamQTH API: {self.API_URL} with params {params}")
                response = requests.get(self.API_URL, params=params, timeout=15)
                logger.debug(f"HamQTH API response status: {response.status_code}")
                response.raise_for_status()

                # Parse CSV response
                csv_text = response.text
                csv_lines = csv_text.strip().split('\n')
                logger.debug(f"HamQTH API returned {len(csv_lines)} spots")

                # Cache the results
                self._cache = {
                    "key": cache_key,
                    "data": csv_lines
                }
                self._cache_time = current_time

            # Calculate time threshold
            now = datetime.utcnow()
            time_threshold = now - timedelta(minutes=minutes)

            # Filter spots
            filtered_spots = []
            for line in csv_lines:
                try:
                    # Skip empty lines
                    if not line.strip():
                        continue

                    # Parse CSV line (delimiter is ^)
                    # Actual format: "DXCall^Freq^Spotter^Comment^DateTime^LoTW^eQSL^??^Continent^Band^Country^DXCC"
                    fields = line.split('^')
                    if len(fields) < 10:
                        logger.debug(f"Skipping line with insufficient fields: {line[:50]}")
                        continue

                    dx_call = fields[0].strip()
                    freq_str = fields[1].strip()
                    spotter = fields[2].strip()
                    comment = fields[3].strip()
                    datetime_str = fields[4].strip()
                    spot_band = fields[9].strip().lower() if len(fields) > 9 else ""

                    # Parse frequency
                    try:
                        freq_khz = float(freq_str)
                    except ValueError:
                        continue

                    # Parse time (format: "2153 2025-11-05" which is "HHMM YYYY-MM-DD")
                    try:
                        spot_time = datetime.strptime(datetime_str, "%H%M %Y-%m-%d")
                    except ValueError:
                        logger.debug(f"Could not parse time: {datetime_str}")
                        continue

                    # Check if spot is within time window
                    if spot_time < time_threshold:
                        continue

                    # Try to extract mode from comment
                    spot_mode = ""
                    comment_upper = comment.upper()
                    for mode_type, mode_list in self.MODE_ALIASES.items():
                        for m in mode_list:
                            if m in comment_upper:
                                spot_mode = m
                                break
                        if spot_mode:
                            break

                    # Filter by mode if specified
                    if mode and spot_mode and not self._mode_matches(spot_mode, mode):
                        continue

                    # Calculate age in minutes
                    age_minutes = int((now - spot_time).total_seconds() / 60)

                    # Add filtered spot (only essential fields to reduce token usage)
                    filtered_spots.append({
                        "dx_call": dx_call,
                        "frequency": freq_khz,
                        "band": spot_band or "unknown",
                        "mode": spot_mode or "Unknown",
                        "spotter": spotter,
                        "comment": comment[:50],  # Limit comment length
                        "time": datetime_str.split()[1] if ' ' in datetime_str else datetime_str,  # Just time part
                        "age_minutes": age_minutes
                    })

                except (ValueError, IndexError) as e:
                    logger.debug(f"Skipping malformed spot: {e}")
                    continue

            # Sort by time (most recent first)
            filtered_spots.sort(key=lambda x: x["age_minutes"])

            # Limit number of spots to reduce token usage
            total_count = len(filtered_spots)
            max_return = count if count is not None else self.max_spots
            filtered_spots = filtered_spots[:max_return]

            logger.info(f"Found {total_count} DX spots, returning {len(filtered_spots)}")

            result = json.dumps({
                "band": band or "all",
                "mode": mode or "all",
                "time_window_minutes": minutes,
                "total_spots": total_count,
                "returned_spots": len(filtered_spots),
                "spots": filtered_spots
            })

            logger.debug(f"Returning {len(result)} bytes of DX cluster data")
            return result

        except requests.RequestException as e:
            logger.error(f"HamQTH API request error: {e}")
            return json.dumps({
                "error": f"Failed to fetch DX spots: {str(e)}"
            })
        except Exception as e:
            logger.error(f"DX Cluster error: {e}", exc_info=True)
            return json.dumps({
                "error": f"Error processing DX spots: {str(e)}"
            })

    def get_tool_definition(self) -> Dict:
        """
        Get Claude API tool definition for DX Cluster

        Returns:
            Tool definition dictionary
        """
        return {
            "name": "dx_cluster",
            "description": "Fetch current DX cluster spots showing active amateur radio stations. Returns a list of stations (callsigns) currently on the air with their frequencies, bands, modes, and comments from spotters. You can filter by band (e.g., '20m', '40m') and mode (e.g., 'CW', 'SSB', 'FT8'). Use this when users ask about DX spots, what's on the air, cluster spots, or activity on specific bands/modes like '20m CW' or '17m SSB'.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "band": {
                        "type": "string",
                        "description": "Amateur radio band to filter (e.g., '20m', '40m', '80m'). Leave empty for all bands.",
                        "enum": ["", "160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m", "2m"]
                    },
                    "mode": {
                        "type": "string",
                        "description": "Operating mode to filter (e.g., 'CW', 'SSB', 'FT8', 'RTTY'). Leave empty for all modes. Supports aliases: 'ssb'=phone modes, 'digital'=all digital modes.",
                        "enum": ["", "CW", "SSB", "FT8", "FT4", "RTTY", "PSK", "digital", "phone"]
                    },
                    "minutes": {
                        "type": "integer",
                        "description": "How many minutes back to look for spots (default: 30, max: 120)",
                        "default": 30
                    }
                },
                "required": []
            }
        }

    def execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """
        Execute tool call from Claude

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool result as string
        """
        if tool_name == "dx_cluster":
            band = tool_input.get("band", None)
            if band == "":
                band = None
            mode = tool_input.get("mode", None)
            if mode == "":
                mode = None
            minutes = tool_input.get("minutes", 30)
            # Cap minutes at 120
            minutes = min(minutes, 120)
            return self.get_spots(band=band, mode=mode, minutes=minutes)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
