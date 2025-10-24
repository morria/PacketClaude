# POTA Spots Tool

PacketClaude includes a POTA (Parks on the Air) spots tool that allows Claude to fetch current park activations from the POTA API.

## What is POTA?

Parks on the Air (POTA) is an amateur radio award program that encourages portable operation from parks and public lands. The POTA spots tool provides real-time information about which operators are currently activating parks.

## Features

- **Real-time spots**: Fetches current POTA activations from the official API
- **Band filtering**: Filter spots by amateur radio band (20m, 40m, etc.)
- **Time filtering**: Show spots from the last X minutes (default: 30)
- **Automatic band detection**: Converts frequencies to band names
- **Rich information**: Includes activator callsign, park reference, location, mode, and comments

## Configuration

POTA spots are controlled in `config/config.yaml`:

```yaml
pota:
  # Enable/disable POTA spots tool
  enabled: true
```

### Options:

- **enabled**: Set to `true` to enable POTA spots, `false` to disable

## Usage

Once enabled, Claude can automatically fetch POTA spots when you ask relevant questions:

**Examples:**
```
> What POTA spots are on 20m?
> Show me current POTA activations
> Are there any parks on the air on 40m?
> Who's activating parks right now?
> POTA spots on 15m from the last hour
```

Claude will automatically:
1. Recognize POTA-related queries
2. Call the POTA spots tool with appropriate filters
3. Parse the results
4. Provide a formatted, concise summary

## Tool Parameters

When Claude uses the POTA spots tool, it can specify:

- **band** (optional): Amateur radio band to filter
  - Options: 160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m, 10m, 6m, 2m
  - Default: All bands

- **minutes** (optional): How many minutes back to look for spots
  - Default: 30 minutes
  - Range: Typically 15-120 minutes

## Example Response

When you ask "What POTA spots are on 20m?", Claude might respond with:

```
Here are the current POTA spots on 20m:

1. W1XYZ @ 14.250 MHz (SSB)
   Park: US-1234 - Example State Park
   Location: Massachusetts
   Time: 14:23 UTC
   Comments: Looking for SSB contacts

2. K2ABC @ 14.057 MHz (CW)
   Park: US-5678 - Example National Forest
   Location: Colorado
   Time: 14:20 UTC

Found 15 total spots on 20m in the last 30 minutes.
```

## Information Provided

For each POTA spot, you'll receive:

- **Activator callsign**: Who is activating the park
- **Frequency**: Frequency in kHz and band (e.g., 20m)
- **Mode**: Operating mode (SSB, CW, FT8, etc.)
- **Park reference**: POTA park ID (e.g., US-1234)
- **Park name**: Full name of the park
- **Location**: Geographic location description
- **Time**: When the spot was posted (UTC)
- **Comments**: Any additional information from the spotter

## API Information

The tool uses the official POTA API:
- **Endpoint**: `https://api.pota.app/spot/activator`
- **Update frequency**: Real-time (spots appear immediately)
- **No authentication required**: Free, public API

## Performance Considerations

- API calls typically take 1-2 seconds
- Data is fetched in real-time (not cached)
- Over packet radio, expect longer response times due to transmission
- Consider using band filters to reduce response length

## Supported Bands

The tool automatically detects these amateur radio bands:

| Band | Frequency Range |
|------|----------------|
| 160m | 1.8 - 2.0 MHz |
| 80m  | 3.5 - 4.0 MHz |
| 60m  | 5.3 - 5.4 MHz |
| 40m  | 7.0 - 7.3 MHz |
| 30m  | 10.1 - 10.15 MHz |
| 20m  | 14.0 - 14.35 MHz |
| 17m  | 18.068 - 18.168 MHz |
| 15m  | 21.0 - 21.45 MHz |
| 12m  | 24.89 - 24.99 MHz |
| 10m  | 28.0 - 29.7 MHz |
| 6m   | 50.0 - 54.0 MHz |
| 2m   | 144.0 - 148.0 MHz |

## Use Cases

Perfect for:
- **Hunters**: Finding parks to contact
- **Activators**: Checking what parks are active
- **Contest operators**: Finding multipliers
- **Band conditions**: Seeing what bands are active
- **DX hunters**: Finding rare park activations

## Disabling POTA Tool

To disable the POTA spots tool:

1. Edit `config/config.yaml`
2. Set `pota.enabled: false`
3. Restart PacketClaude

When disabled, Claude won't have access to current POTA spots.

## Troubleshooting

**No spots returned:**
- Check internet connectivity
- Verify API is accessible: `curl https://api.pota.app/spot/activator`
- Try a longer time window (e.g., 60 minutes)
- Check if any parks are currently active

**Tool not working:**
- Ensure `pota.enabled: true` in config
- Check logs for error messages
- Verify `requests` package is installed: `pip install requests`

**Slow responses:**
- API calls add 1-2 seconds to response time
- Over packet radio, this means longer airtime
- Consider asking for specific bands only
- Use shorter time windows (15-30 minutes)

## Privacy & Logging

- POTA API calls are logged in PacketClaude activity logs
- No personal POTA data is stored
- Spots are real-time from the public POTA database
- Rate limiting still applies to overall queries

## Testing

To test the POTA tool independently:

```bash
source .venv/bin/activate
python scripts/test_pota.py
```

This will:
- Fetch all current spots
- Filter by 20m and 40m
- Display sample spots
- Verify band conversion
- Test tool definition
