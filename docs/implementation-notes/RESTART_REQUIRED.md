# RESTART REQUIRED

## Important: PacketClaude Must Be Restarted

The POTA tool has been optimized to fix the token overload issue, but **PacketClaude must be restarted** for the changes to take effect.

### What Changed

The POTA spots tool was returning too much data (~3,741 tokens), which exhausted Claude's token budget before it could respond. This has been fixed by:

1. **Limiting spots returned**: Now returns max 10 spots (configurable)
2. **Removing unnecessary fields**: Stripped down to essential data only
3. **Compressed format**: Reduced from ~15KB to ~1.5KB (89% reduction)

### How to Restart

1. **Stop the current PacketClaude instance**:
   - Press `Ctrl+C` in the terminal where it's running
   - Or: `pkill -f packetclaude`

2. **Start PacketClaude again**:
   ```bash
   ./scripts/run.sh
   ```

   Or:
   ```bash
   source .venv/bin/activate
   python -m src.packetclaude.main
   ```

### Verification

After restarting, the logs should show:
```
POTA spots tool enabled
```

And when POTA is called, you should see:
```
Fetching POTA spots (band=20m, minutes=30)
Found 63 POTA spots, returning 10
```

### Test After Restart

Connect via telnet and try:
```bash
telnet localhost 8023
> show me pota spots on 20m
```

Claude should now successfully return the spots with a helpful response.

### If Still Having Issues

1. Check logs: `tail -f logs/*.log`
2. Verify config: `grep pota config/config.yaml -A 2`
3. Test tool directly: `python scripts/test_pota.py`
4. See `docs/TROUBLESHOOTING.md` for more help

## Current Status

✅ POTA tool optimized (89% token reduction)
✅ Configuration updated (max_spots: 10)
✅ Tests passing
⚠️  **RESTART NEEDED** to apply changes
