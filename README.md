# MIRROR AI — Politician Mirror App

A Streamlit-based paper trading dashboard that tracks the portfolios of elite investors and politicians, scores their holdings by conviction and position size, and lets you one-click approve or reject $500 paper trades via Alpaca.

---

## What it does

Tracks and mirrors the publicly disclosed stock trades of the **top 7 US politicians** ranked by portfolio returns (Unusual Whales 2024 data):

| Rank | Politician | 2024 Return |
|---|---|---|
| 1 | Nancy Pelosi | +70.9% |
| 2 | David Rouzer | +149.0% |
| 3 | Ron Wyden | +123.8% |
| 4 | Pete Sessions | +77.5% |
| 5 | Susan Collins | +77.5% |
| 6 | Tommy Tuberville | top active trader |
| 7 | Marjorie Taylor Greene | +30.2% |

1. **Fetches** all STOCK Act trade disclosures from the public House and Senate data feeds
2. **Filters** for the top 7 target politicians only
3. **Scores** each ticker: buy disclosures add weight, sell disclosures subtract; weighted by politician track record; cross-politician conviction multiplier
4. **Surfaces** the top 10 buy signals in a feed you can approve or reject
5. **Executes** approved trades as fractional market orders on Alpaca (paper mode by default)
6. **Tracks** open positions, unrealized P&L, and a politician leaderboard

---

## Project structure

```
Polmirap/
├── app.py                  # Streamlit UI — feed, positions, leaderboard
├── fetcher.py              # Fetches + scores congressional STOCK Act disclosures
├── scorer.py               # Re-scores from cached data without re-fetching
├── strategy.py             # Position sizing (MirrorStrategy)
├── lambda_function.py      # AWS Lambda for automated trade mirroring
├── database.py             # DynamoDB deduplication helper
├── politician_trades.json  # Cached raw trades (output of fetcher.py)
├── suggestions.json        # Scored top-10 signals (output of fetcher.py / scorer.py)
└── manifest.json           # PWA manifest
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

Each ticker is scored from STOCK Act buy/sell disclosures:

```
score += (buy_count - sell_count) × politician_weight
```

- **Politician weights:** Pelosi 1.6 › Rouzer 1.4 › Tuberville/Collins/Wyden 1.3 › Sessions 1.2 › Greene 1.1
- **Conviction multiplier:** ×1.5 if bought by 3+ politicians, ×1.2 if bought by 2+
- Only net-buy positions (more buys than sells) surface as signals

---

## Automated trading (Lambda)

`lambda_function.py` is an AWS Lambda handler that:
- Fetches the House & Senate congressional trade disclosures from public S3 buckets
- Filters for a configurable list of target politicians
- Deduplicates via DynamoDB before executing each trade on Alpaca
- Runs on a schedule (CloudWatch Events) for near-real-time mirroring of Periodic Transaction Reports (PTRs)

Set `DRY_RUN=True` to simulate without placing orders.

---

## Notes

- Run `fetcher.py` daily (before market open) to keep signals fresh — STOCK Act requires disclosure within 45 days so data is not real-time
- `politician_trades.json` is the raw cache; delete it and re-run `fetcher.py` to get the latest
- Paper trading is always on by default; set `DRY_RUN=False` in Lambda env only when ready for live execution
