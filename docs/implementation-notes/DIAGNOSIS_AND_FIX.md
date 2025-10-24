# POTA Tool Issue: Diagnosis & Fix

## Problem Confirmed

Claude reports "experiencing technical difficulties with the POTA spots tool"

## Root Cause Identified

**The running PacketClaude process is using OLD CODE from before the optimization.**

### Evidence:

1. **Log shows old code**:
   ```
   "Executing tool: pota_spots" (line 113)
   ```

2. **Current code is different**:
   ```python
   logger.info(f"Executing tool: {tool_name} with input: {tool_input}")  # line 113
   ```

3. **Tool logs missing**:
   - No "Fetching POTA spots" messages
   - No "Found X spots, returning Y" messages
   - No POTA API request logs

4. **Direct test works**:
   ```bash
   $ python scripts/test_pota.py
   ✓ All tests passed!
   ```

## The Old Code Problem

The OLD unoptimized POTA tool returns ~15KB of data (~3,741 tokens) which exhausts Claude's token budget before it can respond.

## The Solution

### **RESTART PacketClaude** to load the optimized code

```bash
# 1. Stop PacketClaude
#    Press Ctrl+C in the terminal where it's running
#    Or find and kill the process:
ps aux | grep packetclaude
kill <PID>

# 2. Start PacketClaude with new code
./scripts/run.sh

# Or manually:
source .venv/bin/activate
python -m src.packetclaude.main
```

### After Restart - Verify Fix

**Check logs for the NEW code**:
```bash
tail -f logs/packetclaude_*.log
```

You should see:
```
"Executing tool: pota_spots with input: {'band': '20m'}"  # Note "with input"
"Fetching POTA spots (band=20m, minutes=30)"
"POTA API response status: 200"
"Found 63 POTA spots, returning 10"
"Returning 1509 bytes of POTA data"
```

**Test via telnet**:
```bash
telnet localhost 8023
> show me pota spots on 20m
```

Claude should now successfully respond with spots!

## What Changed (Already in Code)

✅ **Optimized POTA tool** - 89% token reduction
- Returns max 10 spots (configurable)
- Removed unnecessary fields
- Compressed time format
- Result: ~1,500 bytes (~377 tokens) instead of ~15,000 bytes (~3,741 tokens)

✅ **Added comprehensive logging**
- API request/response status
- Data size tracking
- Error details with stack traces

✅ **Configuration added**
```yaml
pota:
  enabled: true
  max_spots: 10
```

## Why Restart is Required

Python loads modules into memory when the process starts. Changes to `.py` files don't affect running processes. You must:

1. **Stop** the old process
2. **Start** a new process to load the new code

## Troubleshooting After Restart

If still having issues:

1. **Verify new code is running**:
   ```bash
   grep "with input" logs/packetclaude_*.log | tail -1
   ```
   Should show recent timestamp with "with input" in the message

2. **Check POTA tool logs appear**:
   ```bash
   grep "Fetching POTA spots" logs/packetclaude_*.log
   ```
   Should show POTA API calls

3. **Test tool directly**:
   ```bash
   python scripts/test_pota.py
   python scripts/check_startup.py
   ```

4. **Check for errors**:
   ```bash
   grep -i error logs/packetclaude_*.log | tail -20
   ```

## Summary

- ✅ Code is fixed and optimized
- ✅ Tests pass successfully
- ✅ Configuration is correct
- ⚠️ **RESTART REQUIRED** - Old process is still running
- 🎯 After restart, POTA tool will work correctly

**Once you restart, the issue will be resolved!**
