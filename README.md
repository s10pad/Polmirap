# MIRROR AI

Monitor public trade disclosures from politicians, executives, and high-profile investors — scoring, ranking, and surfacing actionable signals.

The project has two parts:

- **`web/`** — Next.js 15 frontend (the user-facing app + landing page)
- **`mirror_ai/`** — Python/Streamlit backend (the trading engine: fetch → score → execute → track)

---

## What it does

Tracks and mirrors the publicly disclosed stock trades of the **top US politicians** ranked by portfolio returns (Unusual Whales 2024 data):

| Rank | Politician | 2024 Return |
|------|-----------|-------------|
| 1 | Nancy Pelosi | +70.9% |
| 2 | David Rouzer | +149.0% |
| 3 | Ron Wyden | +123.8% |
| 4 | Pete Sessions | +77.5% |
| 5 | Susan Collins | +77.5% |
| 6 | Tommy Tuberville | top active trader |
| 7 | Marjorie Taylor Greene | +30.2% |

1. **Fetches** STOCK Act trade disclosures from public House/Senate feeds (Brave Search)
2. **Filters** for target roster members
3. **Scores** each ticker — buys add weight, sells subtract; weighted by track record + cross-member conviction
4. **Surfaces** the top buy signals in a feed you approve or reject
5. **Executes** approved trades as fractional orders on Alpaca (paper mode by default)
6. **Tracks** open positions, P&L, and a leaderboard

---

## Repository Structure

```
Polmirap/
├── web/                    # Next.js 15 frontend
│   ├── app/
│   │   ├── layout.tsx      # Root layout — ThemeProvider (dark)
│   │   ├── page.tsx        # Landing page (SPECTRAL aesthetic)
│   │   └── globals.css     # Design tokens, keyframes, utilities
│   ├── components/ui/
│   │   └── dotted-surface.tsx   # Three.js animated dot-grid background
│   ├── lib/utils.ts        # cn() helper (clsx + tailwind-merge)
│   ├── tailwind.config.ts  # Syncopate / Barlow / DM Mono fonts + animations
│   └── package.json
│
├── mirror_ai/              # Python / Streamlit backend
│   ├── app.py              # Streamlit dashboard (DASHBOARD, FEED, POSITIONS, ROSTER, LEADERBOARD, WATCHLIST, LOGS)
│   ├── agent.py            # AI trading agent (Gemini)
│   ├── fetcher.py          # Disclosure fetcher (Brave Search)
│   ├── scorer.py           # Signal scoring engine
│   ├── roster.py           # Roster management
│   ├── scheduler.py        # APScheduler daily run
│   ├── strategy.py         # Position sizing rules
│   ├── memory.py           # Firestore persistence
│   ├── notifier.py         # Telegram alerts
│   ├── requirements.txt
│   ├── railway.toml        # Railway deploy config
│   └── docs/
│       ├── PLAN.md         # Phased implementation plan
│       ├── STRATEGY.md     # Trading strategy (locked)
│       └── CHANGELOG.md    # Append-only action log
│
├── screenshot.mjs          # Puppeteer screenshot tool (design QA)
├── package.json            # Root — puppeteer only
└── README.md
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | 18+ |
| Python | 3.11+ |
| npm | 9+ |

---

## Running the frontend (`web/`)

```bash
cd web
npm install
npm run dev        # http://localhost:4000  (hot reload)
# or
npm run build && npm run start
```

---

## Running the backend (`mirror_ai/`)

```bash
cd mirror_ai

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

Create `mirror_ai/.env` (see `.env.example` for the full list):

```env
ALPACA_KEY=
ALPACA_SECRET=
ALPACA_PAPER=true                       # set false for live money

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

GEMINI_API_KEY=
BRAVE_SEARCH_API_KEY=

FIREBASE_PROJECT_ID=polmirap-25a9a
FIREBASE_CREDENTIALS_PATH=serviceAcountKey.JSON   # local file path
# On Railway, paste the whole key as one line instead:
# FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}

AUTONOMY_MODE=controlled
VETO_WINDOW_HOURS=2
STOP_LOSS_PCT=15
MAX_POSITION_PCT=7
SECTOR_CAP_PCT=20
```

```bash
streamlit run app.py            # http://localhost:8501
```

> **Secrets never live in the repo.** `.env` and `serviceAcountKey.JSON` are git-ignored.

---

## Deployment

### Backend — Railway

`mirror_ai/railway.toml` is pre-configured (Nixpacks, Streamlit start command, healthcheck at `/_stcore/health`). Connect the GitHub repo, set root directory to `mirror_ai/`, add every `.env` key in the Variables tab (use `FIREBASE_CREDENTIALS_JSON` for the service account), deploy.

### Frontend — Vercel

```bash
cd web && npx vercel
```

Or connect the repo to Vercel with root directory `web/`.

---

## Design System (frontend)

- **Fonts:** Syncopate (display), Barlow Condensed (subheads), Barlow (body), DM Mono (data)
- **Palette:** near-black `#030b14`, teal `#00d4aa`, sky `#38bdf8`, violet `#a78bfa`
- **Background:** Three.js animated particle grid + grain overlay
- **Motion:** `transform` + `opacity` only; spring easing; IntersectionObserver scroll-reveal

---

## Screenshot tool

```bash
node screenshot.mjs http://localhost:4000          # capture the running frontend
node screenshot.mjs http://localhost:4000 label    # with a label suffix
```

Requires `npm install` at the repo root (installs Puppeteer).
