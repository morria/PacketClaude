# QRZ Callsign Lookup Tool for Claude

The QRZ tool allows users to ask Claude to look up amateur radio callsigns and get detailed information about operators.

## Overview

When enabled, users can ask Claude questions about any amateur radio callsign and Claude will automatically use the QRZ tool to fetch information from QRZ.com.

## Features

- **Operator Information**: Name, location, license class
- **Address Details**: Full address if available in QRZ database
- **Coordinates**: Latitude/longitude and grid square
- **License Info**: License class and expiration date
- **Contact Info**: Email address (if public)
- **Aliases**: Alternative callsigns

## Setup

### Prerequisites

The QRZ tool requires QRZ.com credentials (same as authentication system).

1. **Get QRZ.com Account**: Free account at https://www.qrz.com/
2. **Optional: Subscribe to XML Logbook Data**: $39.95/year for API key access

### Configuration

Add QRZ credentials to your `.env` file:

**Option 1: API Key (Recommended)**
```bash
QRZ_API_KEY=your_api_key_here
```

**Option 2: Username/Password (Free)**
```bash
QRZ_USERNAME=your_qrz_username
QRZ_PASSWORD=your_qrz_password
```

The tool will automatically enable when QRZ credentials are present.

## Usage Examples

Users can ask Claude questions like:

### Simple Lookup
```
User: Look up callsign W1AW
Claude: [Uses QRZ tool to fetch information]
       W1AW is Hiram Percy Maxim in CT, United States.
       License: Extra, Grid: FN31pr
```

### Natural Language
```
User: What can you tell me about K1TTT?
Claude: [Uses QRZ tool]
       K1TTT is John Doe in Massachusetts...
```

### Multiple Callsigns
```
User: Compare callsigns W1AW and K1TTT
Claude: [Uses QRZ tool twice]
       W1AW: Hiram Percy Maxim, CT, Extra class...
       K1TTT: John Doe, MA, Extra class...
```

### Location Queries
```
User: Where is N0CALL located?
Claude: [Uses QRZ tool]
       N0CALL is in Kansas, United States. Grid square: EM28
```

## Tool Behavior

### When Enabled
- Tool appears in Claude's available tools
- Claude automatically calls it when users ask about callsigns
- Results are parsed and presented in natural language

### When Disabled
- Tool not available if no QRZ credentials
- Users will see: "QRZ lookup is not enabled"
- Authentication still works with format-only validation

### Error Handling
- **Callsign not found**: Reports callsign not in QRZ database
- **Invalid format**: Still attempts lookup
- **API errors**: Gracefully handles and reports to user
- **Missing credentials**: Returns helpful error message

## What Gets Returned

The tool returns a JSON structure with:

```json
{
  "callsign": "W1AW",
  "found": true,
  "operator": {
    "name": "Hiram Percy Maxim",
    "country": "United States",
    "address": "225 Main Street, CT 06111",
    "license_class": "Extra",
    "license_expires": "2025-12-31",
    "grid_square": "FN31pr",
    "coordinates": {
      "latitude": "41.7658",
      "longitude": "-72.6734"
    },
    "email": "w1aw@arrl.org",
    "aliases": "W1AW/1"
  }
}
```

Claude then formats this into natural language for the user.

## Privacy Considerations

### What's Queried
- Only callsigns explicitly mentioned by users
- Queries go to QRZ.com's public database
- Same data available on QRZ.com website

### What's NOT Shared
- User's conversation with Claude
- User's own callsign (unless they ask Claude to look it up)
- Any other session data

### QRZ Privacy
- QRZ database shows only publicly-available amateur radio license data
- Email addresses only shown if operator made them public on QRZ
- Same privacy policy as QRZ.com website

## Testing

Test the QRZ tool integration:

```bash
# Make sure you have QRZ credentials in .env
source .venv/bin/activate
python scripts/test_qrz_tool.py
```

Expected output:
```
======================================================================
QRZ Tool Integration Test
======================================================================

Testing QRZ Tool for Claude

1. Tool Description:
----------------------------------------------------------------------
Tool Name: qrz_lookup
Description: Look up amateur radio callsign information from QRZ.com...
Required Parameters: ['callsign']

2. Valid Callsign Lookup (W1AW):
----------------------------------------------------------------------
✓ Found: W1AW
  Name: Hiram Percy Maxim
  Country: United States
  License Class: Extra
  Grid Square: FN31pr

...
```

## Troubleshooting

### Tool Not Available
**Symptom**: Claude says "I don't have access to QRZ lookup"

**Cause**: QRZ credentials missing or invalid

**Fix**:
```bash
# Check .env file has credentials
cat .env | grep QRZ

# Add credentials if missing
echo "QRZ_API_KEY=your_key" >> .env

# Restart PacketClaude
./scripts/run.sh
```

### "QRZ lookup is not enabled"
**Symptom**: Tool returns this error when Claude tries to use it

**Cause**: QRZ credentials not loaded

**Fix**: Same as above - check .env and restart

### Callsign Not Found
**Symptom**: Tool reports callsign not found

**Causes**:
1. Callsign doesn't exist (never issued)
2. Callsign expired/cancelled
3. Typo in callsign

**Verification**: Check on https://www.qrz.com/ directly

### API Errors
**Symptom**: "Error looking up callsign"

**Causes**:
1. QRZ.com API is down
2. Network connectivity issues
3. Invalid API key/credentials
4. Rate limit exceeded

**Check logs**:
```bash
tail -f logs/packetclaude_*.log | grep -i qrz
```

## Implementation Details

### Files

- **Tool**: `src/packetclaude/tools/qrz_tool.py`
- **Lookup Client**: `src/packetclaude/auth/qrz_lookup.py`
- **Test Script**: `scripts/test_qrz_tool.py`

### Integration

The tool is automatically registered with Claude when QRZ credentials are present:

```python
# In main.py
if self.config.qrz_enabled:
    qrz_tool = QRZTool(
        qrz_lookup=self.qrz_lookup,
        enabled=True
    )
    tools.append(qrz_tool)
```

### Tool Schema

The tool provides this schema to Claude:

```python
{
    "name": "qrz_lookup",
    "description": "Look up amateur radio callsign information from QRZ.com...",
    "input_schema": {
        "type": "object",
        "properties": {
            "callsign": {
                "type": "string",
                "description": "The amateur radio callsign to look up"
            }
        },
        "required": ["callsign"]
    }
}
```

Claude automatically knows when to use this tool based on user queries.

## Benefits

1. **Enhanced User Experience**: Users can easily look up callsigns
2. **Natural Language**: No need to remember special commands
3. **Integrated**: Claude handles formatting and presentation
4. **Comprehensive**: Returns all available operator information
5. **Flexible**: Works with any valid amateur radio callsign

## Limitations

1. **Requires QRZ Subscription**: API key method requires paid subscription
2. **Rate Limits**: Subject to QRZ.com API rate limits
3. **Data Availability**: Only returns data available in QRZ database
4. **No Caching**: Each lookup hits QRZ.com API (no local cache)

## Future Enhancements

Possible improvements:

1. **Local Caching**: Cache recent lookups to reduce API calls
2. **Batch Lookups**: Support looking up multiple callsigns at once
3. **FCC ULS Integration**: Alternative data source for US callsigns
4. **Historical Data**: Track license changes over time
5. **Proximity Search**: Find callsigns near a location
6. **Activity Data**: Integration with log data from QRZ Logbook

## See Also

- [QRZ Authentication](QRZ_AUTHENTICATION.md) - QRZ authentication system
- [Tools Documentation](TOOLS.md) - Overview of all Claude tools
- [QRZ.com XML API](https://www.qrz.com/XML/current_spec.html) - Official API docs

---

**Note**: This tool shares QRZ credentials with the authentication system. Only one set of credentials is needed for both features.
