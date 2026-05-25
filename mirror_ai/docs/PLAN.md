# MIRROR AI — Claude Code Implementation Plan

> This document is a session-by-session work plan for Claude Code.
> Work through phases in order. Each phase has a clear goal, affected files, and step-by-step tasks.
> Check off tasks as you complete them. Never skip a phase unless the owner says so.

---

## How to start each session

1. Read this file top to bottom first.
2. Find the first uncompleted `[ ]` task.
3. Read the files listed under "Affected files" for that phase before writing any code.
4. Do the work, then mark tasks `[x]`.
5. Write a brief entry to `docs/CHANGELOG.md` summarizing what changed.

---

## Phase 1 — Deploy to Railway (Streamlit backend)

**Goal:** `mirror_ai/` is live at a public Railway URL. Everything else depends on this.

**Affected files:** `railway.toml`, `.env.example`, `app.py`, `requirements.txt`

**Context:**
- `railway.toml` is already correctly configured with Nixpacks builder, the right start command, and health check path `/_stcore/health`.
- State is in Firestore (not disk), so Railway restarts are safe.
- The app needs these env vars set in Railway's Variables tab before it will start successfully.

**Tasks:**

- [ ] **Verify `railway.toml` is correct.** Confirm start command is:
  ```
  streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
  ```
  and `healthcheckPath = "/_stcore/health"`. It is — no changes needed.

- [ ] **Check `.env.example` is complete.** Open `.env.example` and confirm every variable the app reads via `os.getenv()` is listed. Scan `app.py`, `memory.py`, `fetcher.py`, `agent.py`, `notifier.py`, `scheduler.py` for any `os.getenv` calls not yet in `.env.example`. Add missing ones.

- [ ] **Add a `FIREBASE_CREDENTIALS_JSON` env var path.** `memory.py` reads `FIREBASE_CREDENTIALS_JSON` (JSON string) or `FIREBASE_CREDENTIALS_PATH` (file path). On Railway, use the JSON string approach — the service account key file cannot be committed to the repo. Document this in `.env.example`:
  ```
  # Paste the entire contents of serviceAccountKey.json as a single-line JSON string
  FIREBASE_CREDENTIALS_JSON=
  ```

- [ ] **Confirm `requirements.txt` is complete.** Run `pip install -r requirements.txt` locally and verify no import errors on startup. Add any missing packages.

- [ ] **Instruct owner:** Push `mirror_ai/` to GitHub → Railway → New Project → Deploy from GitHub. Set root directory to `mirror_ai/`. Add all env vars from `.env` in Railway Variables tab. Deploy. Confirm health check passes at `https://<your-app>.railway.app/_stcore/health`.

- [ ] **Test the live URL.** Navigate to the Railway URL. Confirm the dashboard loads, sidebar shows portfolio metrics (or a clear Alpaca error if keys aren't set yet), and all 7 tabs render without Python errors.

---

## Phase 2 — Backtesting module

**Goal:** A new "Backtest" tab in the dashboard. Given a roster member and a date range, compute: "If you had mirrored this person's disclosed trades for the last N months, what would your return have been?"

**Affected files:** `app.py`, `fetcher.py`, `strategy.py` (read only), new file `backtest.py`

**Context:**
- Disclosure data comes from Brave Search (`fetcher.py`). For backtesting, we need historical disclosure dates and trade prices — use Alpaca historical bars (`get_alpaca_bars`) for the entry/exit prices.
- The scorer in `scorer.py` already has all the logic for sizing. Backtest should reuse it in "simulation" mode.
- Keep it simple first: calculate entry price on disclosure date, exit price 30/60/90 days later (or current price if still within window). Compute return.

**New file: `backtest.py`**

```python
# backtest.py
# Simulate mirroring a roster member's disclosed trades over a historical period.
# Input:  member name, list of (ticker, disclosure_date) tuples, exit_days (30/60/90)
# Output: list of trade results with entry/exit prices and return%, plus summary stats
```

**Tasks:**

- [ ] **Create `backtest.py`** with a `simulate_member(name, trades, exit_days=60)` function:
  - For each `(ticker, disclosure_date)`: call `get_alpaca_bars(ticker, days=exit_days+30)` to get price history around that date.
  - Find the bar on or just after `disclosure_date` → that is `entry_price`.
  - Find the bar `exit_days` later → that is `exit_price`. If no bar (future date), use the latest available price.
  - Compute `return_pct = (exit_price - entry_price) / entry_price * 100`.
  - Return a list of dicts: `{ticker, entry_date, entry_price, exit_date, exit_price, return_pct}`.
  - Also return summary: `total_return_pct` (compound), `win_rate`, `avg_return`, `best_trade`, `worst_trade`.

- [ ] **Add a `render_backtest()` function to `app.py`:**
  - Inputs: selectbox for roster member, slider for exit window (30 / 60 / 90 days).
  - Load member's historical signals from Firestore (`get_pending_signals()` filtered by member name — note: these only go back as far as signals were stored, not forever).
  - Display a results table with Plotly: cumulative return curve over time.
  - Show summary stats in stat cards: total return %, win rate, best/worst trade.
  - Add an empty state if no historical signals exist for that member yet.

- [ ] **Add "📈 Backtest" as the 8th tab** in `main()`:
  ```python
  tabs = st.tabs([..., "📈 Backtest"])
  with tabs[7]: render_backtest()
  ```

- [ ] **Gate it clearly.** If fewer than 5 signals exist for the selected member, show a message: "Not enough historical signals yet — backtest becomes meaningful after ~2 weeks of live operation."

---

## Phase 3 — Capitol Trades-style disclosure cards

**Goal:** Replace the current signal cards in the Feed tab with richer structured cards that show: ticker, action (BUY/SELL), estimated amount range, filing date vs. trade date, committee membership, and a direct link to the source filing.

**Affected files:** `app.py` (render_feed), `agent.py` (signal extraction prompt), `memory.py` (signal schema)

**Context:**
- Current signal schema (stored in Firestore `pending_signals`): `{signal_id, ticker, action, score, conviction, reasoning, buyers: [{name, portfolio_pct}], position_pct, position_usd, sector, status}`.
- Capitol Trades cards add: `amount_range` (e.g. "$15,001–$50,000"), `filing_date`, `trade_date`, `source_url`, `committee` (for politicians).
- These new fields need to be extracted by the AI in `agent.py` and stored in the signal dict.

**Tasks:**

- [ ] **Extend signal schema.** In `agent.py`, find the prompt that instructs the AI to extract trade data. Add instructions to also extract:
  - `trade_date` — date the trade actually occurred (from the filing)
  - `filing_date` — date the disclosure was filed
  - `amount_range` — the dollar range disclosed (e.g. "$15,001–$50,000")
  - `source_url` — URL of the filing or news source
  - `committee` — congressional committee membership if applicable (politicians only)
  - `lag_days` — integer: `filing_date - trade_date` in days (the disclosure lag)

  Update the JSON schema in the prompt to include these fields with `null` as the fallback.

- [ ] **Update the signal card HTML in `render_feed()`** in `app.py`. Replace the current card body with a two-column layout:
  - **Left column:** Ticker + action badge + price + sparkline (keep existing)
  - **Right column:** Structured metadata grid:
    - Trade date / Filed date / Lag badge (color red if lag > 45 days — suspicious)
    - Amount range badge
    - Committee (if present)
    - Source link (small, opens in new tab)
  - Keep the reasoning text and buyers list below both columns.
  - Keep the approve/skip/watchlist buttons unchanged.

- [ ] **Add a lag warning badge.** If `lag_days > 45`, show `⚠️ LATE FILING` in amber next to the filing date. Capitol Hill trades filed late are often more meaningful (trying to hide something).

- [ ] **Backfill gracefully.** Old signals won't have the new fields. Handle `None`/missing gracefully in the HTML — just omit those rows rather than showing "None".

---

## Phase 4 — TradingView chart embeds per ticker

**Goal:** Every ticker in the Feed and Watchlist tabs gets a live candlestick chart, not just a sparkline SVG.

**Affected files:** `app.py` (render_feed, render_watchlist)

**Context:**
- TradingView offers free embeddable lightweight chart widgets via `https://s3.tradingview.com/tv.js` — no API key needed.
- Streamlit can render iframes via `st.components.v1.html()`.
- The lightweight-charts library from TradingView is MIT licensed and can be bundled inline.

**Tasks:**

- [ ] **Create a `tradingview_chart(ticker, height=300)` helper function** in `app.py`:
  - Returns an HTML string containing a self-contained TradingView Mini Widget embed:
    ```html
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
      <div id="tv_{ticker}"></div>
      <script src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
      {
        "symbol": "{ticker}",
        "width": "100%",
        "height": {height},
        "locale": "en",
        "dateRange": "3M",
        "colorTheme": "dark",
        "trendLineColor": "#00d4aa",
        "underLineColor": "rgba(0,212,170,0.08)",
        "isTransparent": true,
        "autosize": true,
        "largeChartUrl": ""
      }
      </script>
    </div>
    <!-- TradingView Widget END -->
    ```
  - Render via `st.components.v1.html(html_str, height=height+20, scrolling=False)`.

- [ ] **Add chart to signal cards in `render_feed()`:**
  - Inside the news expander for each signal, add a `st.expander(f"📊 Chart — ${ticker}")` that calls `tradingview_chart(ticker, height=250)`.
  - Do not auto-expand — keep it collapsed by default so the feed doesn't get cluttered.

- [ ] **Add chart to each watchlist item in `render_watchlist()`:**
  - Below each `watch-card` row, add a collapsed `st.expander(f"📊 {ticker}")` with the chart.

- [ ] **Test on mobile.** Open the Railway URL on a phone. Confirm the charts are scrollable and not overflowing. If they overflow, set `width="100%"` and cap the iframe height explicitly.

---

## Phase 5 — Real-money execution

**Goal:** Safely switch from paper trading to live Alpaca. This phase should only be started after Phase 1 is stable and the owner has reviewed paper trading results.

**Affected files:** `app.py` (sidebar), `.env.example`, `agent.py`, `strategy.py`

**⚠️ RISK NOTE:** This phase involves real money. Every change must include an explicit confirmation dialog. Do not auto-execute anything. Do not proceed with this phase until the owner explicitly instructs you to start it.

**Tasks:**

- [ ] **Add a live/paper mode indicator to the sidebar.** Read `ALPACA_PAPER` env var. If `false`, show a persistent red `🔴 LIVE TRADING` banner in the sidebar. If `true`, show `📄 PAPER MODE` in gray. This makes it impossible to forget which mode is active.

- [ ] **Add confirmation dialogs to all order submission paths.** In `agent.py` and anywhere `client.submit_order()` is called: wrap in a two-step confirm that shows the exact order details (ticker, qty, estimated dollar value, current price) and requires a second click labeled "Confirm — place real money order."

- [ ] **Add limit order support.** Currently all orders are market orders. Add an `ORDER_TYPE` env var (default `market`). When set to `limit`, submit limit orders at last price ± 0.1% slippage buffer instead of market orders. Add this to `.env.example` with documentation.

- [ ] **Add trailing stop support.** After a position is entered in live mode, submit a trailing stop order at `TRAILING_STOP_PCT` (default `8`) percent below the current price. This provides automatic downside protection without requiring a manual `EXIT` command. Add to `.env.example`.

- [ ] **Document the live switchover steps** in `README.md`:
  1. Create live Alpaca API keys at alpaca.markets (separate from paper keys)
  2. Set `ALPACA_KEY` and `ALPACA_SECRET` to live keys in Railway Variables
  3. Set `ALPACA_PAPER=false`
  4. Set `ALPACA_BASE_URL=https://api.alpaca.markets`
  5. Fund the Alpaca account
  6. Keep `AUTONOMY_MODE=controlled` — never start live trading in full-auto mode
  7. Redeploy on Railway

- [ ] **Regulatory note:** Add a comment in `agent.py` near the order submission code:
  ```python
  # LEGAL NOTE: This system executes trades based on publicly disclosed information
  # (STOCK Act filings, SEC disclosures). It does NOT use material non-public
  # information (MNPI). All source data is from public filings with a minimum lag.
  # Review FINRA Rule 4511 and SEC Rule 17a-3 if operating as anything other than
  # a purely personal account. This is not financial advice.
  ```

---

## Bonus tasks (do after all phases complete, in any order)

These are lower priority but high value. Pick them up when a phase is done and the next phase is blocked.

### B1 — P&L attribution per politician

In `render_positions()` and the new Backtest tab, show which politician signal generated each open position and what that person's running return is. This data is already in `positions_meta` (Firestore) as `triggered_by`. Wire it to member performance from `get_member_performance()`.

### B2 — Watchlist push alerts

When a roster member trades a ticker that's on the owner's watchlist, send a Telegram message immediately (don't wait for scoring). In `agent.py` or `scheduler.py`, after disclosure parsing, check each extracted ticker against `get_watchlist()`. If there's a match, call `notifier.py` with a dedicated watchlist-hit message template.

### B3 — Sector heatmap tab

New tab "🗺️ Sectors" in `app.py`. Use Plotly's treemap chart (`go.Treemap`) to visualize current portfolio allocation by sector. Color by P&L: green = positive, red = negative. Size by market value. Data comes from `get_alpaca_account()` positions + `get_open_positions_meta()` sector field.

### B4 — PWA manifest for phone home screen

Add a `manifest.json` and a `<link rel="manifest">` tag via `st.markdown()` in `app.py`. This lets users add the Railway URL to their phone home screen and have it open full-screen like a native app. Minimum required fields: `name`, `short_name`, `start_url`, `display: standalone`, `background_color`, `theme_color`, `icons`.

```json
{
  "name": "Mirror AI",
  "short_name": "MirrorAI",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#030b14",
  "theme_color": "#00d4aa",
  "icons": [{"src": "https://placehold.co/192x192/030b14/00d4aa?text=M", "sizes": "192x192", "type": "image/png"}]
}
```

Inject it as a `<head>` injection via:
```python
st.markdown('<link rel="manifest" href="/manifest.json">', unsafe_allow_html=True)
```
Note: Streamlit doesn't serve static files by default — you'll need to add a FastAPI static file route or use a Cloudflare Worker to serve `manifest.json` from the same origin.

### B5 — Leaderboard rolling return chart

In `render_leaderboard()`, when a member profile is opened (drilldown view), add a Plotly line chart showing their cumulative mirrored return over time. Data: filter `get_pending_signals()` for signals involving this member where `status == "approved"`, join to `get_open_positions_meta()` for entry dates and exit data. Plot the equity curve.

---

## What NOT to do

- Do not touch `STRATEGY.md` or the rules in `strategy.py` without explicit owner approval. The strategy document states: "Any modification requires owner edits + a new deployment + a CHANGELOG entry."
- Do not commit `serviceAccountKey.json`, `.env`, or any file containing secrets.
- Do not implement WebSocket live feeds or a Redis cache layer — the current Firestore + `@st.cache_data` approach is sufficient until traffic justifies the added complexity.
- Do not build a separate Next.js frontend. The FOLLOWUP.md mentions a `web/` directory but it doesn't exist yet. Focus on the Streamlit app. If the owner wants to add Next.js later, that is a separate project.

---

## Environment variables reference (complete)

Add any missing ones to Railway Variables and `.env.example`:

| Variable | Required | Used in |
|---|---|---|
| `ALPACA_KEY` | Yes | `app.py`, `fetcher.py`, `agent.py` |
| `ALPACA_SECRET` | Yes | `app.py`, `fetcher.py`, `agent.py` |
| `ALPACA_PAPER` | Yes | `app.py`, `agent.py` — `true`/`false` |
| `ALPACA_BASE_URL` | No | Override for live vs paper endpoint |
| `TELEGRAM_BOT_TOKEN` | Yes | `notifier.py` |
| `TELEGRAM_CHAT_ID` | Yes | `notifier.py` |
| `CLAUDE_API_KEY` | Yes | `agent.py` |
| `BRAVE_SEARCH_API_KEY` | Yes | `fetcher.py` |
| `FIREBASE_CREDENTIALS_JSON` | Yes (Railway) | `memory.py` — full JSON string |
| `FIREBASE_PROJECT_ID` | Yes | `memory.py` — e.g. `polmirap-25a9a` |
| `GOOGLE_GENAI_API_KEY` | If used | `agent.py` — Gemini fallback |
| `AUTONOMY_MODE` | No | Default `controlled` |
| `VETO_WINDOW_HOURS` | No | Default `2` |
| `STOP_LOSS_PCT` | No | Default `15` |
| `MAX_POSITION_PCT` | No | Default `7` |
| `SECTOR_CAP_PCT` | No | Default `20` |
| `ORDER_TYPE` | No (Phase 5) | Default `market` |
| `TRAILING_STOP_PCT` | No (Phase 5) | Default `8` |
