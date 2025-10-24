"""
QRZ callsign lookup tool for Claude
Allows users to look up amateur radio callsigns
"""
import logging
import json
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class QRZTool:
    """
    QRZ callsign lookup tool for Claude
    Provides callsign information lookups to users
    """

    def __init__(self, qrz_lookup, enabled: bool = True):
        """
        Initialize QRZ tool

        Args:
            qrz_lookup: QRZLookup instance for performing lookups
            enabled: Enable/disable QRZ functionality
        """
        self.qrz_lookup = qrz_lookup
        self.enabled = enabled

    def get_tool_description(self) -> Dict:
        """
        Get tool description for Claude

        Returns:
            Tool description in Anthropic format
        """
        return {
            "name": "qrz_lookup",
            "description": (
                "Look up amateur radio callsign information from QRZ.com. "
                "Returns operator name, location, license class, and other details. "
                "Use this when users ask about a specific callsign or want to know "
                "information about a ham radio operator."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "callsign": {
                        "type": "string",
                        "description": "The amateur radio callsign to look up (e.g., W1AW, K1TTT)"
                    }
                },
                "required": ["callsign"]
            }
        }

    def lookup_callsign(self, callsign: str) -> str:
        """
        Look up a callsign on QRZ.com

        Args:
            callsign: Callsign to look up

        Returns:
            JSON string with callsign information or error
        """
        if not self.enabled:
            return json.dumps({
                "error": "QRZ lookup is not enabled",
                "message": "QRZ.com integration is currently disabled"
            })

        logger.info(f"QRZ tool: Looking up callsign {callsign}")

        try:
            # Validate and clean callsign
            callsign = callsign.upper().strip()

            # Look up on QRZ
            result = self.qrz_lookup.lookup(callsign)

            if result is None:
                return json.dumps({
                    "callsign": callsign,
                    "found": False,
                    "message": f"Callsign {callsign} not found in QRZ database"
                })

            # Format the response with useful information
            response = {
                "callsign": result.get('call', callsign),
                "found": True,
                "operator": {}
            }

            # Add name information
            if result.get('fullname'):
                response['operator']['name'] = result['fullname']
            elif result.get('fname') or result.get('name'):
                fname = result.get('fname', '')
                lname = result.get('name', '')
                response['operator']['name'] = f"{fname} {lname}".strip()

            # Add location information
            location_parts = []
            if result.get('addr1'):
                location_parts.append(result['addr1'])
            if result.get('addr2'):
                location_parts.append(result['addr2'])

            city_state_zip = []
            if result.get('state'):
                city_state_zip.append(result['state'])
            if result.get('zip'):
                city_state_zip.append(result['zip'])

            if city_state_zip:
                location_parts.append(' '.join(city_state_zip))

            if result.get('country'):
                response['operator']['country'] = result['country']

            if location_parts:
                response['operator']['address'] = ', '.join(location_parts)

            # Add license information
            if result.get('class'):
                response['operator']['license_class'] = result['class']

            if result.get('expires'):
                response['operator']['license_expires'] = result['expires']

            # Add grid square and coordinates
            if result.get('grid'):
                response['operator']['grid_square'] = result['grid']

            if result.get('lat') and result.get('lon'):
                response['operator']['coordinates'] = {
                    'latitude': result['lat'],
                    'longitude': result['lon']
                }

            # Add email if available
            if result.get('email'):
                response['operator']['email'] = result['email']

            # Add any aliases
            if result.get('aliases'):
                response['operator']['aliases'] = result['aliases']

            logger.info(f"QRZ tool: Successfully looked up {callsign}")
            return json.dumps(response, indent=2)

        except Exception as e:
            logger.error(f"QRZ tool error looking up {callsign}: {e}", exc_info=True)
            return json.dumps({
                "callsign": callsign,
                "error": "Lookup failed",
                "message": f"Error looking up callsign: {str(e)}"
            })

    def execute(self, callsign: str) -> str:
        """
        Execute the tool (compatibility method)

        Args:
            callsign: Callsign to look up

        Returns:
            JSON string with results
        """
        return self.lookup_callsign(callsign)

    def execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """
        Execute tool call from Claude

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters

        Returns:
            JSON string with results
        """
        if tool_name == "qrz_lookup":
            callsign = tool_input.get("callsign", "")
            if not callsign:
                return json.dumps({
                    "error": "Missing parameter",
                    "message": "Callsign parameter is required"
                })
            return self.lookup_callsign(callsign)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
