# MIRROR AI v2

Mirror AI is a personal stock trading system that watches what successful public figures — politicians, executives, athletes — are publicly disclosing about their stock trades, and automatically mirrors those trades in your own brokerage account. It is built for one owner and runs continuously in the cloud.

The system uses public disclosure data (STOCK Act filings, SEC filings, and news) to detect when someone on your roster buys a stock. It scores that signal based on how many people are buying the same ticker, how trusted each person is, and how large their position appears to be. It then proposes a proportionally sized trade in your Alpaca account, notifies you via Telegram, and waits for you to veto it before executing. If you don't veto within the configured window, it executes automatically.

Every decision — who is on the roster, what was traded, why, and what happened — is written to a persistent changelog. The roster is reviewed weekly by the AI, which proposes additions, removals, or weight changes based on recent performance and fresh search data.

---

## What it does, step by step

1. Every weekday at 7:30am ET, the system searches the web for recent trade disclosures from everyone on your roster.
2. Claude parses the raw search results and extracts structured trades: ticker, buy/sell, estimated size, sector.
3. Trades are scored. Tickers bought by multiple people get a higher score. Each person's weight (how much you trust their trades) multiplies into the score.
4. Signals above the threshold are sized to your portfolio using the conviction caps (1 person = up to 1%, 2 people = up to 2.5%, 3+ people = up to 5%).
5. You get a Telegram message for each signal. You have a configurable veto window (default 2 hours). Reply `SKIP TICKER` to block it.
6. After the veto window, any unblocked signals are executed as market orders on Alpaca.
7. Every hour during market hours, positions are checked against the stop loss threshold. If a position is down more than `STOP_LOSS_PCT` from entry, you get an alert.
8. Every Monday at 6am ET, the AI reviews the roster using fresh search data and proposes up to 3 changes. You approve via Telegram or the dashboard.

---

## Setup from scratch

### 1. Clone and install

```bash
git clone <your-repo>
cd Polmirap/mirror_ai
pip install -r requirements.txt
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Fill in every value. See the variable reference below.

### 3. Set up Alpaca

- Create an account at alpaca.markets
- Go to Paper Trading and create API keys
- Set `ALPACA_PAPER=true` in your `.env` while testing
- When ready for live trading, create live API keys and set `ALPACA_PAPER=false`

### 4. Set up Telegram

- Message @BotFather on Telegram → `/newbot` → follow prompts → copy the token
- Message @userinfobot to find your personal chat ID
- Set both values in `.env`

### 5. Set up Claude AI

- Go to console.anthropic.com → API Keys → Create Key
- Set `CLAUDE_API_KEY` in `.env`

### 6. Set up Brave Search

- Go to api.search.brave.com → create an account → Subscriptions → get API key
- Set `BRAVE_SEARCH_API_KEY` in `.env`

### 7. Set up Upstash Redis

- Go to upstash.com → Create Database → copy the REST URL and token
- Set both values in `.env`

### 8. Run locally

```bash
streamlit run app.py
```

The dashboard opens at http://localhost:8501. The background scheduler starts automatically.

---

## Environment variable reference

| Variable | Required | Description |
|---|---|---|
| `ALPACA_KEY` | Yes | Your Alpaca API key |
| `ALPACA_SECRET` | Yes | Your Alpaca API secret |
| `ALPACA_PAPER` | Yes | `true` for paper trading, `false` for live |
| `TELEGRAM_BOT_TOKEN` | Yes | From @BotFather — the bot's API token |
| `TELEGRAM_CHAT_ID` | Yes | Your personal chat ID — where alerts go |
| `CLAUDE_API_KEY` | Yes | Anthropic API key for AI parsing and reasoning |
| `BRAVE_SEARCH_API_KEY` | Yes | Brave Search API key for disclosure lookups |
| `UPSTASH_REDIS_REST_URL` | Yes | Upstash Redis REST endpoint |
| `UPSTASH_REDIS_REST_TOKEN` | Yes | Upstash Redis auth token |
| `AUTONOMY_MODE` | No | `controlled` (default) or `full` — see below |
| `VETO_WINDOW_HOURS` | No | Hours to wait for veto. Default: `2` |
| `STOP_LOSS_PCT` | No | % drop that triggers stop loss alert. Default: `15` |
| `MAX_POSITION_PCT` | No | Hard cap per position as % of portfolio. Default: `7` |
| `SECTOR_CAP_PCT` | No | Max % of portfolio in any single sector. Default: `20` |

---

## Controlled vs Full autonomy

**CONTROLLED mode** (default and recommended) means every trade signal is sent to you via Telegram first. You have `VETO_WINDOW_HOURS` (default 2 hours) to reply `SKIP TICKER` to block it. If you do nothing, the trade executes after the window expires.

**FULL mode** means trades with a score above `FULL_MODE_AUTO_THRESHOLD` (currently 8.0) execute immediately without waiting for your response. Lower-scored signals still go through the veto window. Use this only if you are comfortable with the scoring system and have tested it in paper trading mode first.

To switch modes:
- Via Telegram: `SET MODE FULL` or `SET MODE CONTROLLED`
- Via dashboard: sidebar toggle
- There is a confirmation step in the dashboard to prevent accidental activation

---

## Telegram command reference

| Command | What it does |
|---|---|
| `SKIP TICKER` | Veto a pending trade. Example: `SKIP AAPL` |
| `APPROVE` | Apply the current weekly roster review proposal |
| `EXIT TICKER` | Close an open position. Example: `EXIT MSFT` |
| `HOLD TICKER` | Dismiss a stop loss alert and keep the position |
| `STATUS` | Show portfolio equity, buying power, roster size |
| `SET MODE FULL` | Switch to full autonomy mode |
| `SET MODE CONTROLLED` | Switch back to controlled mode |
| `HELP` | Show the full command list |

---

## Guide to other docs files

- **AGENT.md** — What the AI can do, what requires your approval, and escalation rules
- **SKILL.md** — How scoring works in plain English, with worked examples
- **MEMORY.md** — Auto-updated file showing current roster members and their performance
- **STRATEGY.md** — The full rulebook: position sizing, stop loss, sector caps, rebalancing
- **CHANGELOG.md** — Append-only log of every action the system takes
- **REVIEW.md** — Weekly roster review template and latest proposal

---

## Railway deployment

1. Push your code to a GitHub repo
2. Go to railway.app → New Project → Deploy from GitHub repo
3. Select your repo and the `Polmirap/mirror_ai` directory (or set root directory in settings)
4. Add all environment variables from your `.env` file in the Railway Variables tab
5. Railway will detect `railway.toml` and use Nixpacks to build
6. The app starts with `streamlit run app.py` on the configured port
7. The `/healthz` endpoint is checked by Railway to confirm the app is alive

The scheduler starts automatically when the Streamlit app starts, so there is no separate worker process needed. Everything runs in one dyno.

If Railway restarts the app, the scheduler restarts with it. Redis holds all persistent state, so nothing is lost between restarts.
