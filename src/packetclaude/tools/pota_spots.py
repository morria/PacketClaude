"""
POTA (Parks on the Air) spots tool for Claude
Fetches current POTA activator spots from the POTA API
"""
import logging
import json
import time
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import requests


logger = logging.getLogger(__name__)


class POTASpotsTool:
    """
    POTA spots tool for fetching park activations
    """

    # POTA API endpoint
    API_URL = "https://api.pota.app/spot/activator"

    # Band definitions (frequency ranges in MHz)
    BANDS = {
        "160m": (1.8, 2.0),
        "80m": (3.5, 4.0),
        "60m": (5.3, 5.4),
        "40m": (7.0, 7.3),
        "30m": (10.1, 10.15),
        "20m": (14.0, 14.35),
        "17m": (18.068, 18.168),
        "15m": (21.0, 21.45),
        "12m": (24.89, 24.99),
        "10m": (28.0, 29.7),
        "6m": (50.0, 54.0),
        "2m": (144.0, 148.0),
    }

    def __init__(self, enabled: bool = True):
        """
        Initialize POTA spots tool

        Args:
            enabled: Enable/disable POTA functionality
        """
        self.enabled = enabled

    def _freq_to_band(self, freq_khz: float) -> Optional[str]:
        """
        Convert frequency in kHz to band name

        Args:
            freq_khz: Frequency in kHz

        Returns:
            Band name (e.g., "20m") or None if not in ham bands
        """
        freq_mhz = freq_khz / 1000.0

        for band, (low, high) in self.BANDS.items():
            if low <= freq_mhz <= high:
                return band

        return None

    def get_spots(self, band: Optional[str] = None, minutes: int = 30) -> str:
        """
        Fetch POTA spots from API

        Args:
            band: Band to filter (e.g., "20m"), None for all bands
            minutes: How many minutes back to look for spots

        Returns:
            JSON string with filtered spots
        """
        if not self.enabled:
            return json.dumps({
                "error": "POTA spots tool is disabled"
            })

        try:
            logger.info(f"Fetching POTA spots (band={band}, minutes={minutes})")

            # Fetch spots from API
            response = requests.get(self.API_URL, timeout=10)
            response.raise_for_status()

            all_spots = response.json()

            # Calculate time threshold
            now = datetime.utcnow()
            time_threshold = now - timedelta(minutes=minutes)

            # Filter spots
            filtered_spots = []
            for spot in all_spots:
                try:
                    # Parse spot time (format: "2024-10-24T14:30:00")
                    spot_time_str = spot.get("spotTime", "")
                    spot_time = datetime.strptime(spot_time_str, "%Y-%m-%dT%H:%M:%S")

                    # Check if spot is within time window
                    if spot_time < time_threshold:
                        continue

                    # Get frequency and determine band
                    freq_khz = float(spot.get("frequency", 0))
                    spot_band = self._freq_to_band(freq_khz)

                    # Filter by band if specified
                    if band and spot_band != band:
                        continue

                    # Add filtered spot with band info
                    filtered_spots.append({
                        "spotter": spot.get("spotter", ""),
                        "activator": spot.get("activator", ""),
                        "frequency": freq_khz,
                        "band": spot_band,
                        "mode": spot.get("mode", ""),
                        "park": spot.get("reference", ""),
                        "park_name": spot.get("name", ""),
                        "location": spot.get("locationDesc", ""),
                        "time": spot_time_str,
                        "comments": spot.get("comments", "")
                    })

                except (ValueError, KeyError) as e:
                    logger.debug(f"Skipping malformed spot: {e}")
                    continue

            # Sort by time (most recent first)
            filtered_spots.sort(key=lambda x: x["time"], reverse=True)

            logger.info(f"Found {len(filtered_spots)} POTA spots")

            return json.dumps({
                "band": band or "all",
                "time_window_minutes": minutes,
                "count": len(filtered_spots),
                "spots": filtered_spots
            })

        except requests.RequestException as e:
            logger.error(f"POTA API request error: {e}")
            return json.dumps({
                "error": f"Failed to fetch POTA spots: {str(e)}"
            })
        except Exception as e:
            logger.error(f"POTA spots error: {e}")
            return json.dumps({
                "error": f"Error processing POTA spots: {str(e)}"
            })

    def get_tool_definition(self) -> Dict:
        """
        Get Claude API tool definition for POTA spots

        Returns:
            Tool definition dictionary
        """
        return {
            "name": "pota_spots",
            "description": "Fetch current POTA (Parks on the Air) activator spots. Returns a list of amateur radio operators currently activating parks. You can filter by band (e.g., '20m', '40m') and time window. Use this when users ask about POTA activations, park activators, or who's on the air in parks.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "band": {
                        "type": "string",
                        "description": "Amateur radio band to filter (e.g., '20m', '40m', '80m'). Leave empty for all bands.",
                        "enum": ["160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m", "2m", ""]
                    },
                    "minutes": {
                        "type": "integer",
                        "description": "How many minutes back to look for spots (default: 30)",
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
        if tool_name == "pota_spots":
            band = tool_input.get("band", None)
            if band == "":
                band = None
            minutes = tool_input.get("minutes", 30)
            return self.get_spots(band=band, minutes=minutes)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
