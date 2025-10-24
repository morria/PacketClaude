"""
Band Conditions Tool for Claude
Provides real-time HF band propagation conditions from HamQSL.com (N0NBH)
"""
import json
import logging
import time
import xml.etree.ElementTree as ET
from typing import Dict, Optional
from datetime import datetime
import urllib.request
import urllib.error


logger = logging.getLogger(__name__)


class BandConditionsTool:
    """
    Tool for fetching and reporting HF band propagation conditions
    Uses the free HamQSL.com (N0NBH) solar data API
    """

    API_URL = "https://www.hamqsl.com/solarxml.php"
    CACHE_DURATION = 3600  # 1 hour in seconds

    def __init__(self, enabled: bool = True):
        """
        Initialize band conditions tool

        Args:
            enabled: Enable/disable band conditions functionality
        """
        self.enabled = enabled
        self._cache = None
        self._cache_time = 0

    def get_tool_definition(self) -> Dict:
        """
        Get Claude API tool definition for band conditions

        Returns:
            Tool definition dictionary
        """
        return {
            "name": "band_conditions",
            "description": (
                "Get current HF amateur radio band propagation conditions and solar indices. "
                "Provides information about which bands are open (80m, 40m, 30m, 20m, 17m, 15m, 12m, 10m), "
                "current solar flux, sunspot numbers, K-index, and geomagnetic conditions. "
                "Use this when users ask about band conditions, propagation, solar activity, "
                "which bands are open, or if a specific band like 20m or 40m is good for operating."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["summary", "solar", "band_detail"],
                        "description": (
                            "Action to perform: 'summary' for overall conditions, "
                            "'solar' for detailed solar indices, "
                            "'band_detail' for specific band information"
                        )
                    },
                    "band": {
                        "type": "string",
                        "description": (
                            "Specific band to query (e.g., '20m', '40m'). "
                            "Only used with band_detail action"
                        )
                    }
                },
                "required": ["action"]
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
        if tool_name == "band_conditions":
            action = tool_input.get("action", "summary")
            band = tool_input.get("band")
            return self.execute(action=action, band=band)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def execute(self, action: str = "summary", band: Optional[str] = None) -> str:
        """
        Execute band conditions query

        Args:
            action: Action to perform (summary, solar, band_detail)
            band: Specific band to query (for band_detail action)

        Returns:
            JSON string with results
        """
        if not self.enabled:
            return json.dumps({
                "success": False,
                "error": "Band conditions tool is disabled"
            })

        try:
            # Fetch data (from cache or API)
            data = self._fetch_data()

            if action == "summary":
                return self._format_summary(data)
            elif action == "solar":
                return self._format_solar_detail(data)
            elif action == "band_detail":
                return self._format_band_detail(data, band)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown action: {action}"
                })

        except Exception as e:
            logger.error(f"Band conditions error: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": f"Failed to fetch band conditions: {str(e)}"
            })

    def _fetch_data(self) -> Dict:
        """
        Fetch data from HamQSL API with caching

        Returns:
            Parsed solar data dictionary
        """
        current_time = time.time()

        # Return cached data if still valid
        if self._cache and (current_time - self._cache_time) < self.CACHE_DURATION:
            logger.debug("Using cached band conditions data")
            return self._cache

        # Fetch fresh data
        logger.info(f"Fetching band conditions from {self.API_URL}")

        try:
            with urllib.request.urlopen(self.API_URL, timeout=10) as response:
                xml_data = response.read().decode('utf-8')
        except urllib.error.URLError as e:
            raise Exception(f"Failed to fetch data from HamQSL: {e}")

        # Parse XML
        try:
            root = ET.fromstring(xml_data)
            data = self._parse_xml(root)
        except ET.ParseError as e:
            raise Exception(f"Failed to parse XML response: {e}")

        # Cache the result
        self._cache = data
        self._cache_time = current_time

        return data

    def _parse_xml(self, root: ET.Element) -> Dict:
        """
        Parse XML response from HamQSL API

        Args:
            root: XML root element

        Returns:
            Dictionary of parsed data
        """
        solar_data = root.find('solardata')
        if solar_data is None:
            raise Exception("Invalid XML structure: missing solardata element")

        def get_text(element, tag, default=""):
            """Helper to safely get element text"""
            elem = element.find(tag)
            return elem.text if elem is not None and elem.text else default

        # Parse band conditions
        band_conditions = {}
        for band_elem in solar_data.findall('.//band'):
            band_name = band_elem.get('name', '')
            band_time = band_elem.get('time', '')
            condition = band_elem.text or 'Unknown'

            if band_name:
                key = f"{band_name}_{band_time}".lower()
                band_conditions[key] = condition

        # Parse VHF conditions
        vhf_conditions = {}
        for phenomenon_elem in solar_data.findall('.//phenomenon'):
            name = phenomenon_elem.get('name', '')
            location = phenomenon_elem.get('location', '')
            if name:
                vhf_conditions[name.lower()] = location

        return {
            'updated': get_text(solar_data, 'updated'),
            'solar_flux': get_text(solar_data, 'solarflux'),
            'sunspots': get_text(solar_data, 'sunspots'),
            'a_index': get_text(solar_data, 'aindex'),
            'k_index': get_text(solar_data, 'kindex'),
            'x_ray': get_text(solar_data, 'xray'),
            'helium_line': get_text(solar_data, 'heliumline'),
            'proton_flux': get_text(solar_data, 'protonflux'),
            'electron_flux': get_text(solar_data, 'electonflux'),
            'solar_wind': get_text(solar_data, 'solarwind'),
            'magnetic_field': get_text(solar_data, 'magneticfield'),
            'aurora': get_text(solar_data, 'aurora'),
            'signal_noise': get_text(solar_data, 'signalnoise'),
            'band_conditions': band_conditions,
            'vhf_conditions': vhf_conditions
        }

    def _format_summary(self, data: Dict) -> str:
        """Format summary of band conditions"""
        conditions = data['band_conditions']

        # Organize bands by day/night
        day_bands = {}
        night_bands = {}

        for key, value in conditions.items():
            if '_day' in key:
                band = key.replace('_day', '')
                day_bands[band] = value
            elif '_night' in key:
                band = key.replace('_night', '')
                night_bands[band] = value

        result = {
            "success": True,
            "updated": data['updated'],
            "solar_summary": {
                "solar_flux": data['solar_flux'],
                "sunspots": data['sunspots'],
                "k_index": data['k_index'],
                "a_index": data['a_index'],
                "x_ray": data['x_ray']
            },
            "band_conditions_day": day_bands,
            "band_conditions_night": night_bands,
            "summary_text": self._generate_summary_text(data, day_bands, night_bands)
        }

        return json.dumps(result, indent=2)

    def _generate_summary_text(self, data: Dict, day_bands: Dict, night_bands: Dict) -> str:
        """Generate human-readable summary text"""
        lines = []
        lines.append(f"Current Band Conditions (Updated: {data['updated']})")
        lines.append(f"Solar Flux: {data['solar_flux']} | Sunspots: {data['sunspots']} | K-Index: {data['k_index']}")
        lines.append("")
        lines.append("HF Bands (Daytime):")

        for band in ['80m-40m', '30m-20m', '17m-15m', '12m-10m']:
            condition = day_bands.get(band, 'Unknown')
            marker = " ★" if condition.lower() in ['good', 'excellent'] else ""
            lines.append(f"  {band}: {condition}{marker}")

        lines.append("")
        lines.append("HF Bands (Nighttime):")

        for band in ['80m-40m', '30m-20m', '17m-15m', '12m-10m']:
            condition = night_bands.get(band, 'Unknown')
            marker = " ★" if condition.lower() in ['good', 'excellent'] else ""
            lines.append(f"  {band}: {condition}{marker}")

        lines.append("")
        lines.append("Data source: HamQSL.com (N0NBH)")

        return "\n".join(lines)

    def _format_solar_detail(self, data: Dict) -> str:
        """Format detailed solar indices"""
        result = {
            "success": True,
            "updated": data['updated'],
            "solar_indices": {
                "solar_flux": data['solar_flux'],
                "sunspots": data['sunspots'],
                "a_index": data['a_index'],
                "k_index": data['k_index'],
                "x_ray": data['x_ray'],
                "helium_line": data['helium_line'],
                "proton_flux": data['proton_flux'],
                "electron_flux": data['electron_flux'],
                "solar_wind": data['solar_wind'],
                "magnetic_field": data['magnetic_field'],
                "aurora": data['aurora']
            },
            "explanation": {
                "solar_flux": "Higher values (>150) indicate better HF propagation",
                "k_index": "0-3 = quiet, 4-5 = unsettled, 6-9 = storm conditions",
                "a_index": "Lower is better for propagation",
                "sunspots": "More sunspots generally mean better HF conditions"
            }
        }

        return json.dumps(result, indent=2)

    def _format_band_detail(self, data: Dict, band: Optional[str]) -> str:
        """Format detailed information about a specific band"""
        if not band:
            return json.dumps({
                "success": False,
                "error": "No band specified. Please specify a band like '20m' or '40m'"
            })

        # Normalize band input (e.g., "20m" -> match "30m-20m")
        band_lower = band.lower().replace('m', 'm')

        conditions = data['band_conditions']
        day_condition = None
        night_condition = None
        matched_band = None

        # Find matching band conditions
        for key, value in conditions.items():
            if band_lower in key:
                if '_day' in key:
                    day_condition = value
                    matched_band = key.replace('_day', '')
                elif '_night' in key:
                    night_condition = value
                    matched_band = key.replace('_night', '')

        if not matched_band:
            return json.dumps({
                "success": False,
                "error": f"Band '{band}' not found. Available bands: 80m-40m, 30m-20m, 17m-15m, 12m-10m"
            })

        result = {
            "success": True,
            "band": matched_band,
            "query": band,
            "conditions": {
                "day": day_condition or "Unknown",
                "night": night_condition or "Unknown"
            },
            "solar_data": {
                "solar_flux": data['solar_flux'],
                "k_index": data['k_index']
            },
            "updated": data['updated']
        }

        return json.dumps(result, indent=2)
