To run the BBS, you'll need to run a TNC for it to connect to.

```
# Run the TNC
./direwolf
```

Before running the BBS, load it's dependencies.

```
# If you haven't already;
python3 -mvenv .venv
source .venv/bin/activate
```

Then run the BBS.

```
./packetclaude.py
```

# Telnet

You may wish to serve the telnet interface via the web.

```
ttyd -p 8080 -W telnet 127.0.0.1 8023
```

and serve it via tailnet.

```
tailscale funnel 8080
```
