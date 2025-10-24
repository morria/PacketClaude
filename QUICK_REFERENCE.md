# PacketClaude Quick Reference Card

## For Operators Connecting to PacketClaude

### How to Connect
```
connect STATION_CALL-10
```

### Available Commands
| Command | Description |
|---------|-------------|
| (just type) | Ask Claude AI a question |
| `help` or `?` | Display help message |
| `status` | Show rate limits and session info |
| `clear` | Clear conversation history |
| `quit` or `bye` or `73` | Disconnect |

### Example Session
```
> connect N0CALL-10
*** CONNECTED to N0CALL-10

Welcome to PacketClaude!
You are now connected to Claude AI via packet radio.

> What is the speed of light?
...
The speed of light is approximately 299,792,458 meters per second.

> status
Rate limits:
Hourly: 1/10 (9 remaining)
Daily: 1/50 (49 remaining)

Session: 2 messages in history

> 73
73! Goodbye.

*** DISCONNECTED
```

### Tips
- Responses may take 2-5 seconds
- Keep questions concise to save airtime
- Conversation context is preserved during session
- Rate limits: 10 queries/hour, 50 queries/day (default)

---

## For System Administrators

### Quick Start
```bash
source venv/bin/activate
./scripts/run.sh
```

### Important Files
| File | Purpose |
|------|---------|
| `.env` | API key and environment |
| `config/config.yaml` | Main configuration |
| `logs/` | Activity logs |
| `data/sessions.db` | SQLite database |

### Common Tasks

**Check Status**
```bash
# If running as service
sudo systemctl status packetclaude

# View logs
tail -f logs/packetclaude_*.log
```

**Restart**
```bash
# Service
sudo systemctl restart packetclaude

# Manual
# Ctrl+C then ./scripts/run.sh
```

**View Database**
```bash
sqlite3 data/sessions.db
.tables
SELECT * FROM queries ORDER BY timestamp DESC LIMIT 10;
.quit
```

**Check Rate Limits**
```bash
sqlite3 data/sessions.db "SELECT callsign, COUNT(*) as queries, MAX(timestamp) as last_query FROM queries WHERE timestamp > datetime('now', '-1 day') GROUP BY callsign;"
```

### Configuration Quickies

**Change Rate Limits**
Edit `config/config.yaml`:
```yaml
rate_limits:
  queries_per_hour: 20  # Increase to 20
  queries_per_day: 100  # Increase to 100
```

**Disable Radio Control**
```yaml
radio:
  enabled: false
```

**Change Response Length**
```yaml
rate_limits:
  max_response_chars: 2048  # Allow longer responses
```

**Adjust Claude Model**
```yaml
claude:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 1000  # More detailed responses
  temperature: 0.5  # More focused responses
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect to Direwolf | `ps aux \| grep direwolf` - make sure it's running |
| API errors | Check `.env` has valid API key |
| Permission denied | `sudo chmod 666 /dev/ttyUSB0` |
| No responses | Check `logs/` for errors |
| Database locked | Stop service, restart |

### Monitoring

**Watch Real-Time Activity**
```bash
tail -f logs/packetclaude_$(date +%Y%m%d).log | grep -E "Connection\|Query\|Response"
```

**Get Statistics**
```bash
sqlite3 data/sessions.db <<EOF
SELECT
  COUNT(DISTINCT callsign) as unique_stations,
  COUNT(*) as total_queries,
  AVG(response_time_ms) as avg_response_ms
FROM queries
WHERE timestamp > datetime('now', '-7 days');
EOF
```

**Most Active Stations**
```bash
sqlite3 data/sessions.db "SELECT callsign, COUNT(*) as queries FROM queries WHERE timestamp > datetime('now', '-7 days') GROUP BY callsign ORDER BY queries DESC LIMIT 10;"
```

### Emergency Procedures

**Stop Immediately**
```bash
sudo systemctl stop packetclaude
# or Ctrl+C if running manually
```

**Clear All Sessions**
```bash
sqlite3 data/sessions.db "DELETE FROM queries; DELETE FROM connections; DELETE FROM rate_limits;"
```

**Reset Configuration**
```bash
cp config/config.yaml.example config/config.yaml
# Edit with your settings
```

### Performance Tuning

**For High Traffic**
- Reduce `max_tokens` in config (faster responses)
- Reduce `max_response_chars` (less airtime)
- Increase rate limits cautiously
- Monitor API costs at console.anthropic.com

**For Low Bandwidth**
```yaml
claude:
  max_tokens: 250  # Shorter responses
rate_limits:
  max_response_chars: 512  # Tighter limit
```

### Backup

**Database**
```bash
cp data/sessions.db data/sessions.db.backup
```

**Configuration**
```bash
tar czf packetclaude-backup-$(date +%Y%m%d).tar.gz config/ .env
```

### Updates

```bash
cd /path/to/PacketClaude
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart packetclaude
```

---

## Contact & Support

- Documentation: See README.md, INSTALL.md, QUICKSTART.md
- Issues: GitHub Issues (if applicable)
- Logs: `logs/packetclaude_*.log`

**73!**
