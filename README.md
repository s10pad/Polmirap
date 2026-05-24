# MIRROR AI

Monitor public trade disclosures from politicians, executives, and high-profile investors — scoring, ranking, and surfacing actionable signals.

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
└── mirror_ai/              # Python backend — Streamlit dashboard
    ├── app.py              # Main Streamlit app (7 tabs: DASHBOARD, FEED, POSITIONS…)
    ├── agent.py            # AI trading agent logic
    ├── fetcher.py          # Trade disclosure fetcher
    ├── scorer.py           # Signal scoring engine
    ├── roster.py           # Politician/executive roster management
    ├── scheduler.py        # APScheduler job runner
    ├── strategy.py         # Trade strategy logic
    ├── memory.py           # Firebase persistence layer
    ├── notifier.py         # Telegram notification dispatch
    ├── requirements.txt    # Python dependencies
    └── railway.toml        # Railway deployment config
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

### 3 — Python backend (Streamlit dashboard)

```bash
cd mirror_ai

# Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env          # if .env.example exists, else create .env manually
```

**Required `.env` keys:**

```env
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets   # or live URL

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

### 4 — Screenshot utility (dev tool)

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

Push to Railway via their CLI or GitHub integration. Set all `.env` keys as Railway environment variables.

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

### Backend (`mirror_ai/`)

| Package | Purpose |
|---------|---------|
| Streamlit | Dashboard UI |
| alpaca-py | Brokerage API (paper + live trading) |
| google-genai | Gemini AI agent |
| firebase-admin | Cloud persistence |
| APScheduler | Background job scheduling |
| plotly | Interactive charts |
| python-telegram-bot | Trade alert notifications |

---

## Design System

The frontend uses the **SPECTRAL** design language:

- **Fonts:** Syncopate (display), Barlow Condensed (subheadings), Barlow (body), DM Mono (data)
- **Palette:** Near-black base (`#030b14`), teal accent (`--spectrum-teal: #00d4aa`), sky accent (`--spectrum-sky: #38bdf8`), violet (`--spectrum-violet: #a78bfa`)
- **Background:** Three.js animated particle grid (`DottedSurface`) + grain texture overlay
- **Crystals:** CSS clip-path pentagon prism + diamond shapes with animated holographic conic-gradient layers
- **Motion:** `transform` + `opacity` only; spring easing; IntersectionObserver scroll-reveal
