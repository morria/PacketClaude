# PacketClaude Troubleshooting Guide

## Tools Not Working

### POTA Spots Tool

**Symptom**: Claude says "I'm experiencing technical difficulties accessing POTA spots"

**Possible Causes**:

1. **POTA API is down or slow**
   ```bash
   # Test the API directly
   curl https://api.pota.app/spot/activator
   ```
   If this fails or times out, the POTA API itself is having issues.

2. **Network connectivity issues**
   ```bash
   # Test network connectivity
   ping api.pota.app
   ```

3. **Tool not enabled**
   - Check `config/config.yaml`: `pota.enabled: true`
   - Restart PacketClaude after changing config

4. **Missing dependencies**
   ```bash
   source .venv/bin/activate
   pip install requests
   ```

**Testing**:
```bash
# Test POTA tool directly
source .venv/bin/activate
python scripts/test_pota.py

# Test tool integration
python scripts/check_startup.py
```

**Check Logs**:
```bash
# View recent logs
tail -f logs/*.log

# Search for POTA-related errors
grep -i pota logs/*.log
grep -i "tool" logs/*.log
```

### Web Search Tool

**Symptom**: Search queries return no results or errors

**Possible Causes**:

1. **DuckDuckGo rate limiting**
   - Wait a few minutes and try again
   - Reduce search frequency

2. **Missing package**
   ```bash
   source .venv/bin/activate
   pip install ddgs
   ```

3. **Tool not enabled**
   - Check `config/config.yaml`: `search.enabled: true`

**Testing**:
```bash
python scripts/test_search.py
```

## Connection Issues

### Telnet Connection Refused

**Symptom**: Cannot connect via telnet

**Solutions**:

1. **Check if telnet is enabled**
   ```bash
   grep -A 3 "^telnet:" config/config.yaml
   ```
   Should show `enabled: true`

2. **Check if port is correct**
   - Default port is 8023
   - Try: `telnet localhost 8023`

3. **Check if PacketClaude is running**
   ```bash
   # Look for PacketClaude process
   ps aux | grep packetclaude
   ```

4. **Check if port is already in use**
   ```bash
   lsof -i :8023
   ```

### AX.25 Connection Issues

**Symptom**: Cannot connect via Direwolf

**Solutions**:

1. **Check Direwolf is running**
   ```bash
   ps aux | grep direwolf
   ```

2. **Verify Direwolf KISS port**
   - Check Direwolf config for KISS TCP port (usually 8001)
   - Verify `config/config.yaml` has matching port

3. **Test Direwolf connection**
   ```bash
   telnet localhost 8001
   ```

## Rate Limiting Issues

**Symptom**: "Rate limit exceeded" messages

**Solutions**:

1. **Check current limits**
   - Type `status` when connected
   - View your hourly/daily usage

2. **Adjust rate limits** in `config/config.yaml`:
   ```yaml
   rate_limits:
     queries_per_hour: 30
     queries_per_day: 100
   ```

3. **Clear session history**
   - Type `clear` to reset conversation
   - Reduces token usage

4. **Disable rate limiting** (for testing):
   ```yaml
   rate_limits:
     enabled: false
   ```

## Performance Issues

### Slow Responses

**Possible Causes**:

1. **Tool calls add latency**
   - Web search: +1-3 seconds
   - POTA spots: +1-2 seconds
   - Multiple tool calls compound

2. **Large responses over packet radio**
   - Reduce `max_response_chars` in config
   - Ask more specific questions

3. **API rate limits**
   - Claude API may be throttling
   - Check Anthropic dashboard

**Solutions**:

1. **Disable unnecessary tools**:
   ```yaml
   search:
     enabled: false  # If you don't need web search
   pota:
     enabled: false  # If you don't need POTA
   ```

2. **Reduce search results**:
   ```yaml
   search:
     max_results: 3  # Instead of 5
   ```

3. **Lower token limits**:
   ```yaml
   claude:
     max_tokens: 300  # Instead of 500
   ```

## Logging and Debugging

### Enable Debug Logging

Edit `main.py` to increase log verbosity:
```python
setup_logging(
    self.config.log_dir,
    log_level="DEBUG",  # Changed from "INFO"
    log_format=self.config.log_format,
    console_output=True
)
```

### Check Logs

```bash
# View all logs
ls -lh logs/

# Tail logs in real-time
tail -f logs/*.log

# Search for errors
grep -i error logs/*.log
grep -i exception logs/*.log
grep -i failed logs/*.log

# Search for specific issues
grep -i "tool" logs/*.log
grep -i "pota" logs/*.log
grep -i "search" logs/*.log
```

### Test Individual Components

```bash
source .venv/bin/activate

# Test POTA tool
python scripts/test_pota.py

# Test search tool
python scripts/test_search.py

# Test tool integration
python scripts/test_tool_integration.py

# Test startup configuration
python scripts/check_startup.py

# Test telnet (if running)
python scripts/test_telnet.py
```

## Configuration Issues

### Config File Not Found

**Symptom**: "Configuration file not found"

**Solution**:
```bash
# Copy example config
cp config/config.yaml.example config/config.yaml

# Edit with your settings
nano config/config.yaml
```

### API Key Issues

**Symptom**: "ANTHROPIC_API_KEY not found"

**Solution**:
```bash
# Create .env file
cp .env.example .env

# Add your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

### Invalid YAML

**Symptom**: YAML parse errors

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# Check for common issues:
# - Tabs instead of spaces
# - Missing colons
# - Incorrect indentation
```

## Common Error Messages

### "Tool execution failed"

**Causes**:
- Network timeout
- API unavailable
- Missing dependency
- Invalid tool parameters

**Solution**:
- Check logs for specific error
- Test tool independently
- Verify network connectivity

### "Invalid callsign format" (Telnet)

This is normal for telnet connections. The rate limiter accepts IP:port format.

### "Connection error: Failed to connect to Direwolf"

**Solutions**:
- Start Direwolf
- Check Direwolf KISS port matches config
- Verify Direwolf config has AGWPORT or KISSPORT enabled

## Getting Help

1. **Check logs first**: `tail -f logs/*.log`
2. **Run tests**: Execute test scripts in `scripts/`
3. **Verify config**: Use `scripts/check_startup.py`
4. **Check GitHub issues**: Report bugs with log excerpts

## Quick Diagnostic Commands

```bash
# Run all tests
source .venv/bin/activate
python scripts/test_pota.py
python scripts/test_search.py
python scripts/check_startup.py

# Check configuration
grep -E "^(pota|search|telnet|claude):" config/config.yaml -A 2

# View recent errors
tail -100 logs/*.log | grep -i error

# Check if services are running
ps aux | grep -E "(packetclaude|direwolf)"

# Test APIs directly
curl https://api.pota.app/spot/activator | head
curl https://duckduckgo.com
```
