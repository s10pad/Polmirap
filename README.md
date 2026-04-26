# MIRROR AI — Politician Mirror App

A Streamlit-based paper trading dashboard that tracks the portfolios of elite investors and politicians, scores their holdings by conviction and position size, and lets you one-click approve or reject $500 paper trades via Alpaca.

---

## What it does

1. **Fetches** holdings data from public sources:
   - SEC EDGAR 13F filings for Warren Buffett, Bill Ackman, Michael Burry, Ray Dalio
   - ARK Invest ARKK ETF holdings for Cathie Wood
   - Capitol Trades / EDGAR for Nancy Pelosi congressional disclosures
   - SEC Form 4 filings for Elon Musk
2. **Scores** every stock across all investors using a weighted formula that rewards portfolio concentration, investor conviction weight, and cross-investor agreement
3. **Surfaces** the top 10 trade signals in a feed you can approve or reject
4. **Executes** approved trades as fractional market orders on Alpaca (paper trading mode by default)
5. **Tracks** open positions and unrealized P&L, and shows a leaderboard of investor signal strength

---

## Project structure

```
Polmirap/
├── app.py              # Streamlit UI — feed, positions, leaderboard
├── fetcher.py          # SEC EDGAR + ARK + Capitol Trades scrapers
├── scorer.py           # Scores & ranks stocks, writes suggestions.json
├── strategy.py         # Position sizing (MirrorStrategy)
├── lambda_function.py  # AWS Lambda handler for automated congressional trade mirroring
├── database.py         # DynamoDB deduplication helper (DuplicateHandler)
├── holdings.json       # Cached investor holdings (output of fetcher.py)
├── suggestions.json    # Scored trade signals (output of scorer.py)
└── manifest.json       # PWA manifest
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | |
| Streamlit | `pip install streamlit` |
| alpaca-py | `pip install alpaca-py` |
| Alpaca account | [alpaca.markets](https://alpaca.markets) — paper trading is free |

**Environment variables required:**

```bash
ALPACA_KEY=your_alpaca_api_key
ALPACA_SECRET=your_alpaca_api_secret
```

Optional (for automated Lambda execution):
```bash
AWS_REGION=us-east-1
DYNAMODB_TABLE=mirror-trades
```

---

## How to launch

### Step 1 — Fetch fresh holdings data

```bash
python fetcher.py
```

This pulls the latest 13F filings, ARK holdings, and congressional disclosures and writes `holdings.json`.

### Step 2 — Score and generate trade signals

```bash
python scorer.py
```

Reads `holdings.json`, scores each stock, and writes the top 10 suggestions to `suggestions.json`.

### Step 3 — Launch the dashboard

```bash
export ALPACA_KEY=your_key
export ALPACA_SECRET=your_secret
streamlit run app.py
```

On Windows (PowerShell):
```powershell
$env:ALPACA_KEY="your_key"
$env:ALPACA_SECRET="your_secret"
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Dashboard tabs

| Tab | Description |
|---|---|
| **FEED** | Pending trade signals with investor breakdown and conviction bar. Approve ($500 paper trade) or Reject each one. |
| **POSITIONS** | All open Alpaca positions with unrealized P&L and per-share cost. |
| **LEADERBOARD** | Investor signal strength ranking, derived from cumulative scores across all suggestions. |

---

## Scoring logic

Each stock receives a score contribution from each investor who holds it:

```
contribution = (position_size / total_portfolio) × investor_weight × rank_bonus × 100
```

- **Investor weights:** Buffett 1.5 › Burry 1.4 › Ackman 1.3 › Dalio 1.2 › Wood 1.1 › Pelosi/Musk 1.0
- **Rank bonus:** top-10 holdings get up to 2× amplification
- **Conviction multiplier:** ×1.5 if held by 3+ investors, ×1.2 if held by 2+

---

## Automated trading (Lambda)

`lambda_function.py` is an AWS Lambda handler that:
- Fetches the House & Senate congressional trade disclosures from public S3 buckets
- Filters for a configurable list of target politicians
- Deduplicates via DynamoDB before executing each trade on Alpaca
- Runs on a schedule (CloudWatch Events) for near-real-time mirroring of Periodic Transaction Reports (PTRs)

Set `DRY_RUN=True` to simulate without placing orders.

---

## Known issues

- `app.py` loads `suggestions.json` from `/home/ubuntu/suggestions.json` (hardcoded Linux path) — update to a relative path for local Windows use
- `holdings.json` is cached; run `fetcher.py` manually or on a cron schedule to keep it fresh
- Pelosi / Musk data scrapers are best-effort; JavaScript-rendered pages may return partial data
- `lambda_function.py` has an incomplete `targets` list (left blank in source)
