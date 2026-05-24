# MIRROR AI

Monitor public trade disclosures from politicians, executives, and high-profile investors — scoring, ranking, and surfacing actionable signals.

---

## What it does

Tracks and mirrors the publicly disclosed stock trades of the **top 7 US politicians** ranked by portfolio returns (Unusual Whales 2024 data):

| Rank | Politician | 2024 Return |
|------|-----------|-------------|
| 1 | Nancy Pelosi | +70.9% |
| 2 | David Rouzer | +149.0% |
| 3 | Ron Wyden | +123.8% |
| 4 | Pete Sessions | +77.5% |
| 5 | Susan Collins | +77.5% |
| 6 | Tommy Tuberville | top active trader |
| 7 | Marjorie Taylor Greene | +30.2% |

1. **Fetches** all STOCK Act trade disclosures from public House and Senate data feeds
2. **Filters** for target politicians only
3. **Scores** each ticker — buy disclosures add weight, sell disclosures subtract; weighted by politician track record; cross-politician conviction multiplier
4. **Surfaces** the top 10 buy signals in a feed you can approve or reject
5. **Executes** approved trades as fractional market orders on Alpaca (paper mode by default)
6. **Tracks** open positions, unrealized P&L, and a politician leaderboard

---

## Repository Structure

```
Polmirap/
├── index.html              # Static landing page (SPECTRAL design system)
├── serve.mjs               # Local dev HTTP server (serves root at :4000)
├── screenshot.mjs          # Puppeteer screenshot utility
├── package.json            # Root package (puppeteer dependency)
│
├── web/                    # Next.js 15 frontend application
│   ├── app/
│   │   ├── layout.tsx      # Root layout — ThemeProvider (dark)
│   │   ├── page.tsx        # Landing page (React, SPECTRAL aesthetic)
│   │   └── globals.css     # Design tokens, keyframes, utility classes
│   ├── components/
│   │   └── ui/
│   │       └── dotted-surface.tsx   # Three.js animated dot grid background
│   ├── lib/
│   │   └── utils.ts        # cn() utility (clsx + tailwind-merge)
│   ├── tailwind.config.ts  # Custom fonts (Syncopate, Barlow, DM Mono) + animations
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── mirror_ai/              # Python backend — Streamlit dashboard (v2)
│   ├── app.py              # Main Streamlit app (7 tabs: DASHBOARD, FEED, POSITIONS…)
│   ├── agent.py            # AI trading agent logic
│   ├── fetcher.py          # Trade disclosure fetcher
│   ├── scorer.py           # Signal scoring engine
│   ├── roster.py           # Politician/executive roster management
│   ├── scheduler.py        # APScheduler job runner
│   ├── strategy.py         # Trade strategy logic
│   ├── memory.py           # Firebase persistence layer
│   ├── notifier.py         # Telegram notification dispatch
│   ├── requirements.txt    # Python dependencies
│   └── railway.toml        # Railway deployment config
│
├── app.py                  # Streamlit UI — feed, positions, leaderboard (v1, root)
├── fetcher.py              # Fetches + scores congressional STOCK Act disclosures (v1)
├── scorer.py               # Re-scores from cached data without re-fetching (v1)
├── strategy.py             # Position sizing — MirrorStrategy (v1)
├── lambda_function.py      # AWS Lambda for automated trade mirroring
├── database.py             # DynamoDB deduplication helper
├── suggestions.json        # Scored top-10 signals (output of fetcher.py)
└── manifest.json           # PWA manifest
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | 18+ |
| Python | 3.11+ |
| npm | 9+ |
| pip | latest |

---

## Starting the App

### 1 — Static landing page (plain HTML)

```bash
# Install root dependencies (Puppeteer — only needed once)
npm install

# Start local HTTP server
node serve.mjs
```

Opens at **http://localhost:4000**

---

### 2 — Next.js frontend

```bash
cd web
npm install
npm run dev        # dev server with hot-reload
# or
npm run start      # production build server
```

Opens at **http://localhost:4000**

To build for production:

```bash
cd web
npm run build
```

---

### 3 — Python backend — Streamlit dashboard (v2, recommended)

```bash
cd mirror_ai

# Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
# Create a .env file in mirror_ai/ with the keys below
```

**Required `.env` keys:**

```env
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets   # switch to live URL for real money

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

GOOGLE_GENAI_API_KEY=
FIREBASE_CREDENTIALS_PATH=serviceAcountKey.JSON
```

```bash
# Run the dashboard
streamlit run app.py
```

Opens at **http://localhost:8501**

---

### 4 — Python backend — root Streamlit app (v1)

```bash
# From repo root
pip install streamlit alpaca-py

export ALPACA_KEY=your_alpaca_api_key
export ALPACA_SECRET=your_alpaca_api_secret
# Windows: set ALPACA_KEY=...

streamlit run app.py
```

Optional (for AWS Lambda automated execution):

```env
AWS_REGION=us-east-1
DYNAMODB_TABLE=mirror-trades
```

---

### 5 — Screenshot utility (dev tool)

```bash
# Capture a screenshot of any local page
node screenshot.mjs http://localhost:4000
node screenshot.mjs http://localhost:4000 label-name

# Output saved to: ./temporary screenshots/screenshot-N[-label].png
```

Requires Puppeteer (installed via root `npm install`).

---

## Deployment

### Backend — Railway

The `mirror_ai/railway.toml` is pre-configured:

```toml
[deploy]
startCommand = "streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true"
healthcheckPath = "/_stcore/health"
```

Connect the GitHub repo to Railway. Set all `.env` keys as Railway environment variables (Settings → Variables).

### Frontend — Vercel (recommended for Next.js)

```bash
cd web
npx vercel
```

Or connect the GitHub repo to Vercel and set the root directory to `web/`.

---

## Key Dependencies

### Frontend (`web/`)

| Package | Purpose |
|---------|---------|
| Next.js 15 | React framework |
| Three.js | WebGL dot-grid background animation |
| next-themes | Dark mode provider |
| Tailwind CSS | Utility-first styling |
| clsx + tailwind-merge | Conditional classname utility |
| lucide-react | Icon set |

### Backend v2 (`mirror_ai/`)

| Package | Purpose |
|---------|---------|
| Streamlit | Dashboard UI |
| alpaca-py | Brokerage API (paper + live trading) |
| google-genai | Gemini AI agent |
| firebase-admin | Cloud persistence |
| APScheduler | Background job scheduling |
| plotly | Interactive charts |
| python-telegram-bot | Trade alert notifications |

### Backend v1 (root)

| Package | Purpose |
|---------|---------|
| Streamlit | Dashboard UI |
| alpaca-py | Brokerage API |
| boto3 | AWS DynamoDB (deduplication) |

---

## Design System

The frontend uses the **SPECTRAL** design language:

- **Fonts:** Syncopate (display), Barlow Condensed (subheadings), Barlow (body), DM Mono (data)
- **Palette:** Near-black base (`#030b14`), teal accent (`#00d4aa`), sky accent (`#38bdf8`), violet (`#a78bfa`)
- **Background:** Three.js animated particle grid (`DottedSurface`) + grain texture overlay
- **Crystals:** CSS clip-path pentagon prism + diamond shapes with animated holographic conic-gradient layers
- **Motion:** `transform` + `opacity` only; spring easing; IntersectionObserver scroll-reveal
