# BBS Games Documentation

## Overview

PacketClaude includes classic BBS "door games" that users can play during their sessions. All games are simulated by Claude AI based on instructions in the system prompt, providing authentic BBS-style gameplay optimized for low-bandwidth packet radio.

## Available Games

### 1. Drugwars
**Command:** `PLAY DRUGWARS`

Classic economics/trading game set in NYC. Players buy and sell goods across 6 locations, trying to maximize profits over 30 game days.

**Game Mechanics:**
- Starting capital: $2,000 cash
- Starting debt: $5,500 to loan shark
- Game duration: 30 days (turns)
- Coat capacity: 100 spaces (expandable)

**Locations:**
1. Bronx
2. Ghetto
3. Central Park
4. Manhattan
5. Coney Island
6. Brooklyn

**Commodities:**
1. Cocaine
2. Heroin
3. Acid
4. Weed
5. Speed
6. Ludes

**Commands:**
- `B [qty] [drug]` - Buy drugs
- `S [qty] [drug]` - Sell drugs
- `J [location]` - Travel to location
- `D [amount]` - Deposit cash in bank
- `W [amount]` - Withdraw from bank
- `L` - Visit loan shark
- `Q` - Quit game

**Random Events:**
- Cop raids
- Finding drugs/cash
- Muggings
- Coat expansion offers
- Price spikes/crashes

**Scoring:**
- < $10k: Bum
- $10k-$50k: Dealer
- $50k-$100k: Kingpin
- > $100k: Drug Lord

### 2. Tradewars
**Command:** `PLAY TRADEWARS`

Space trading and combat game. Similar to Drugwars but in space with sectors and commodities.

**Commodities:**
- Fuel Ore
- Organics
- Equipment

**Features:**
- Travel between sectors
- Trade goods
- Fight pirates
- Build your fleet

### 3. Lemonade Stand
**Command:** `PLAY LEMONADE`

Business simulation running a lemonade stand.

**Mechanics:**
- Buy supplies (lemons, sugar, cups)
- Set pricing
- Weather affects sales
- 30-day game duration

### 4. Blackjack
**Command:** `PLAY BLACKJACK`

Classic casino card game.

**Features:**
- Standard blackjack rules
- Bet virtual money
- Win/loss tracking

### 5. Ham Radio Trivia
**Command:** `PLAY TRIVIA` or `PLAY HAMTRIVIA`

Multiple choice trivia about amateur radio.

**Categories:**
- Regulations
- Operating procedures
- Technical knowledge
- Amateur radio history

## Implementation

Games are **not** separate Python modules. Instead, they are simulated by Claude AI using detailed instructions in the system prompt (`config/system_prompt.txt`).

### How It Works

1. User types `PLAY DRUGWARS`
2. Claude reads the game instructions from the system prompt
3. Claude initializes game state
4. Game state is tracked in the conversation context
5. Claude processes user commands and updates game state
6. Display is rendered in compressed, bandwidth-optimized format

### Game State Tracking

Game state is maintained in the conversation context using a structured format:

```
GAME_STATE:DRUGWARS|DAY:5|CASH:3500|DEBT:5500|BANK:0|LOC:Brooklyn|
INV:weed=5,speed=12|COAT:100|MAXCOAT:100
```

This allows the game to persist across multiple messages in the same session.

### Bandwidth Optimization

All games are designed for 1200 baud packet radio:

- **Target: < 400 chars per game update**
- Single-letter commands (B/S/J/D/W)
- Compressed displays
- Minimal whitespace
- Numbered options for quick selection
- No ASCII art or excessive formatting

### Example Game Session

```
W2ASM-3> play drugwars

=== DRUGWARS - Day 1/30 ===
Location: Brooklyn | Cash: $2000 | Debt: $5500 | Bank: $0
Coat: 0/100

PRICES:
1. Cocaine  $15000  4. Weed     $300
2. Heroin   $5500   5. Speed    $90
3. Acid     $1000   6. Ludes    $11

[B]uy [S]ell [J]et [D]eposit [W]ithdraw [L]oan [Q]uit
> B 20 6

Bought 20 Ludes for $220
Cash: $1780 | Coat: 20/100

> J 4

Traveling to Manhattan...

=== DRUGWARS - Day 2/30 ===
Location: Manhattan | Cash: $1780 | Debt: $5500
Coat: 20/100

PRICES:
1. Cocaine  $16000  4. Weed     $350
2. Heroin   $7000   5. Speed    $95
3. Acid     $2500   6. Ludes    $55

! Addicts buying Ludes at crazy prices! !

[B]uy [S]ell [J]et [D]eposit [W]ithdraw [L]oan [Q]uit
> S 20 6

Sold 20 Ludes for $1100
Cash: $2880 | Coat: 0/100

>
```

## Adding New Games

To add a new game:

1. Edit `config/system_prompt.txt`
2. Add game to the `AVAILABLE GAMES` list in the `<bbs_games>` section
3. Add detailed game mechanics and rules
4. Specify game state tracking format
5. Define commands and display format
6. Ensure bandwidth optimization (< 400 chars)

Example structure:

```xml
<bbs_games>
AVAILABLE GAMES:
[... existing games ...]
X. **NEWGAME** - Brief description

NEWGAME IMPLEMENTATION:
[Game setup, rules, mechanics]

GAME STATE TRACKING:
GAME_STATE:NEWGAME|[state variables]

[Commands and display format]
</bbs_games>
```

## Natural Language Parsing

Games accept flexible input:
- "play drugwars" = `PLAY DRUGWARS`
- "start a game" = `GAMES` (list)
- "buy 10 weed" = `B 10 4`
- "sell all" = `S [quantity] [drug]`
- "go to bronx" = `J 1`

Claude interprets user intent rather than requiring rigid syntax.

## Session Management

- Games save state between messages in the same session
- Typing `QUIT` exits the current game
- Game state is lost when user disconnects
- No persistent high scores (could be added to database if desired)

## Testing Games

To test games:

1. Connect via telnet: `telnet localhost 8023`
2. Enter a test callsign
3. Type `GAMES` to list available games
4. Type `PLAY DRUGWARS` to start
5. Test various commands
6. Verify state tracking across multiple turns
7. Check bandwidth usage (< 400 chars per update)

## Future Enhancements

Possible additions:
- Persistent high score tables
- Multiplayer games
- More game variety (Adventure, Trivia categories)
- Game statistics tracking
- Leaderboards

## Credits

Games inspired by classic BBS door games from the 1980s-90s:
- Drugwars (original by John E. Dell)
- Trade Wars (Gary Martin)
- Classic BBS door game tradition

Implemented using Claude AI for dynamic game simulation optimized for packet radio bandwidth constraints.
