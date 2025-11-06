===============================================================================
PACKETCLAUDE BBS - README & COMMAND REFERENCE
===============================================================================
W2ASM-3 Packet Claude BBS System
Brooklyn, NY - Grid: FN30aq
Sysop: W2ASM

===============================================================================
WHAT IS PACKETCLAUDE?
===============================================================================
PacketClaude is an AI-powered Packet Radio BBS that provides real-time
information lookup, messaging, file transfer, and classic BBS games over
low-bandwidth AX.25 connections. Powered by Claude AI for intelligent
responses to your queries.

===============================================================================
GETTING STARTED
===============================================================================
After connecting via AX.25 or Telnet:
1. Enter your callsign when prompted
2. System validates via QRZ lookup
3. You'll see the welcome banner
4. Type H or HELP for command list
5. Type ? for quick reference

===============================================================================
INFORMATION COMMANDS
===============================================================================
WX [location]         - Weather conditions and forecast
                        Example: WX 11201, WX Brooklyn

PROP                  - HF propagation conditions and solar data
                        Shows SFI, A/K indices, band conditions

POTA                  - Current Parks on the Air activations
                        Shows recent POTA spots with freq/mode

SPOT                  - Current DX cluster spots and activity

DX [band] [mode]      - DX spots for specific band/mode
                        Example: dx 20m cw, cluster 17m ssb

QTH [callsign]        - QRZ callsign lookup
                        Returns name, location, grid square

GRID [call/location]  - Calculate Maidenhead grid square

DIST [grid1] [grid2]  - Distance and bearing between grids
                        Example: DIST FN30aq FN42gg

FREQ [frequency]      - Band plan and allocation information

BAND [band]           - Band plan details
                        Example: BAND 20m

NEWS [topic]          - Search current news/information
                        Example: NEWS solar flare

LOOKUP [topic]        - General information search
                        Example: LOOKUP APRS protocol

TIME                  - Current UTC and local times

===============================================================================
MESSAGE & MAIL COMMANDS
===============================================================================
MAIL                  - Check your personal mailbox
                        Shows unread messages for your callsign

SEND [call] [text]    - Send message to another user's mailbox
                        Example: SEND W1ABC Meet on 146.52 at 2000Z

MSG [call] [text]     - Store session message for callsign

READ [call]           - Read session messages for callsign

LIST                  - List all stored session messages

===============================================================================
FILE TRANSFER COMMANDS (AX.25 YAPP Protocol)
===============================================================================
/files [filter]       - List available files
                        Filters: public, private, shared, mine
                        Example: /files public

/download <id>        - Download file by ID via YAPP
                        Example: /download 5

/fileinfo <id>        - Show detailed file information

/upload               - Start YAPP file upload
                        (AX.25 connections only)

/share <id> <call>    - Share your file with another callsign
                        Example: /share 10 W1ABC

/publicfile <id>      - Make your file publicly available

/deletefile <id>      - Delete your file

Note: File transfers use YAPP protocol over AX.25. Max file size: 100KB
Telnet users can view file info but cannot transfer via YAPP.

===============================================================================
BBS GAMES
===============================================================================
GAMES                 - List all available games

PLAY DRUGWARS         - Classic economics trading game
                        Buy/sell goods in 6 NYC locations
                        30 days to build your empire
                        Start with $2000, try to become Drug Lord!

PLAY TRADEWARS        - Space trading and combat
                        Travel sectors, trade commodities
                        Fight pirates, build your fleet

PLAY LEMONADE         - Lemonade stand business simulation
                        Manage supplies, pricing, weather

PLAY BLACKJACK        - Casino blackjack card game
                        Bet virtual money, track win/loss

PLAY TRIVIA           - Amateur radio trivia quiz
                        Test your ham radio knowledge

QUIT                  - Exit current game (when playing)

Game Tips:
- Games are optimized for low bandwidth
- Use single-letter commands when possible
- Game state saves between messages
- Type QUIT anytime to exit game

===============================================================================
DRUGWARS QUICK REFERENCE
===============================================================================
Starting Stats: $2000 cash, $5500 debt to loan shark, 100 coat spaces

Locations (6):
  1. Bronx          2. Ghetto         3. Central Park
  4. Manhattan      5. Coney Island   6. Brooklyn

Drugs (6):
  1. Cocaine        2. Heroin         3. Acid
  4. Weed           5. Speed          6. Ludes

Commands:
  B [qty] [drug]    - Buy drugs (B 10 weed or B 10 4)
  S [qty] [drug]    - Sell drugs (S 10 weed or S 10 4)
  J [location]      - Jet to new location (J 1 or J bronx)
  D [amount]        - Deposit cash in bank
  W [amount]        - Withdraw from bank
  L                 - Visit loan shark
  Q                 - Quit game

Strategy Tips:
- Buy low, sell high across different locations
- Watch for special events (price spikes)
- Pay off loan shark to avoid trouble
- Expand coat capacity when offered
- Bank money for safety and interest

===============================================================================
TECHNICAL COMMANDS
===============================================================================
CALC [formula]        - Perform RF calculations
                        Examples: CALC vswr 1.5:1 100w
                                 CALC wavelength 14.200

ANT [type]            - Antenna formulas and dimensions

MODE [mode]           - Digital mode information
                        Example: MODE FT8, MODE RTTY

===============================================================================
UTILITY COMMANDS
===============================================================================
HELP or H [command]   - Show help (detailed if command specified)

INFO or I             - System capabilities and info

?                     - Quick command reference

STATUS                - Show your rate limits and session info

CLEAR or RESET        - Clear conversation history

BYE, QUIT, EXIT, 73   - Disconnect from BBS

===============================================================================
FLEXIBLE SYNTAX
===============================================================================
PacketClaude accepts natural language! You don't need exact syntax.

Instead of "WX 11201" you can type:
  - "weather brooklyn"
  - "what's the weather in 11201"
  - "show me weather"

Instead of "POTA" you can type:
  - "pota spots"
  - "show pota activations"
  - "parks on the air"

Instead of "QTH W2ASM" you can type:
  - "lookup W2ASM"
  - "who is W2ASM"
  - "qrz W2ASM"

The AI understands your intent - just ask naturally!

===============================================================================
RATE LIMITS
===============================================================================
To ensure fair access for all users:
- 10 queries per hour per callsign
- 50 queries per day per callsign
- Type STATUS to check your remaining queries
- Rate limits reset hourly/daily

===============================================================================
BANDWIDTH OPTIMIZATION TIPS
===============================================================================
PacketClaude is designed for 1200 baud packet radio:
- Responses are compressed and terse
- Use abbreviations when possible
- Avoid asking follow-up questions in one message
- Single-letter game commands save bandwidth
- File transfers are chunked for reliability

===============================================================================
SESSION MANAGEMENT
===============================================================================
- Conversation context is maintained during your session
- Type CLEAR to reset conversation history
- Sessions may timeout after inactivity
- Your mailbox persists across sessions

===============================================================================
EXAMPLE SESSION
===============================================================================
W2ASM-3> wx 11201
11201: 52F NW12 ptcld | Tonight clr 45F | Thu sunny 58F

W2ASM-3> pota
Current POTA spots:
K1ABC K-0001 14.260 SSB 1823Z
W3XYZ K-0042 7.032 CW 1815Z
[...]

W2ASM-3> mail
You have 2 new messages:
1. W1ABC: Sked tonight 146.52?
2. N2DEF: QSL received 73

W2ASM-3> play drugwars
=== DRUGWARS - Day 1/30 ===
Location: Brooklyn | Cash: $2000 | Debt: $5500
[game starts...]

===============================================================================
TECHNICAL INFORMATION
===============================================================================
Protocol: AX.25 UI frames, YAPP file transfer
Baud Rate: 1200 baud (typical VHF packet)
Max Response: 1024 characters (may be truncated)
AI Model: Claude 3.5 Sonnet (Anthropic)
Software: PacketClaude v1.0
Source: github.com/yourusername/PacketClaude (check with sysop)

===============================================================================
SUPPORT & CONTACT
===============================================================================
Sysop: W2ASM
QTH: Brooklyn, NY (FN30aq)

For technical issues:
- Type HELP for command assistance
- Check STATUS for rate limit info
- Use CLEAR if conversation gets stuck

For feature requests or bugs:
- Contact sysop via packet: W2ASM @ W2ASM-3
- Send message: SEND W2ASM [your message]

===============================================================================
ACKNOWLEDGMENTS
===============================================================================
PacketClaude combines:
- Anthropic Claude AI for intelligent responses
- AX.25 packet radio protocol (amateur radio)
- Direwolf software TNC
- Classic BBS door game heritage
- YAPP file transfer protocol

Built for the amateur radio community to provide useful field-accessible
information services over VHF/UHF packet radio.

===============================================================================
73 DE W2ASM-3
Welcome to PacketClaude - Where AI meets Packet Radio!
===============================================================================
