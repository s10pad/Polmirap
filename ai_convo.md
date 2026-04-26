# MIRROR AI — Project Discussion Log

This file is our shared working document. Every significant decision, open question, known issue, and planned improvement lives here. Update it as we make progress.

---

## Project Status

| Item | Status |
|---|---|
| App running on EC2 | LIVE — http://18.234.219.234:8501 |
| Alpaca paper account | ACTIVE — $100,000 equity |
| Data refresh cron | ACTIVE — weekdays 08:30 UTC |
| Git repo | https://github.com/s10pad/Polmirap |
| HTTPS / custom domain | NOT YET |
| Lambda auto-trading | NOT DEPLOYED |

---

## What works today

- **Politicians** — scrapes Capitol Trades live for 7 targets (Pelosi, Rouzer, Wyden, Sessions, Collins, Tuberville, Greene). Real trades, real tickers, refreshed daily.
- **Superinvestors** — pulls SEC 13F quarterly filings for 7 fund managers (Buffett, Ackman, Burry, Dalio, Tepper, Paulson, Loeb). Data is quarterly by nature.
- **Athletes** — curated static portfolio based on public filings and confirmed investments. Updated manually each quarter.
- **Sectors** — curated top ETF holdings for 7 sectors (AI, Defence, Energy, Healthcare, Biotech, Financials, Infrastructure). Updated manually each quarter.
- **Feed** — approve/reject per category with $500 paper trade execution via Alpaca.
- **Positions** — live unrealised P&L from Alpaca.
- **Leaderboard** — signal strength ranking for all 4 categories.

---

## Known Issues & Improvement Backlog

Priority order: fix first → fix next → fix when time allows → future

Each item has an estimated fix time for context.

---

### CRITICAL — Fix First

**[1] CEO tickers have bad entries (SPDR, TR, COS, HLDG)**
- *Why:* OpenFIGI CUSIP-to-ticker resolution fails for many holdings (ETFs, foreign-listed), and the name-parsing fallback picks up noise words.
- *Fix:* Replace failed resolutions with a curated known-ticker map for the most common Buffett/Dalio/Ackman holdings, same approach as athletes.
- *Est. time:* 1 hour

**[2] Sector signals — conviction always 1**
- *Why:* Each sector is treated as a single "investor", so cross-sector conviction multiplier never fires. NVDA appears in AI, Defence, and Biotech but gets no boost.
- *Fix:* Aggregate sector signals by ticker across all 7 sectors before scoring, same as politicians.
- *Est. time:* 45 minutes

**[3] Athlete data never auto-refreshes**
- *Why:* Athlete portfolios are hardcoded. No scraper exists for athlete investment news.
- *Fix plan A (cheap):* Quarterly manual review — review public filings and interviews each quarter, update the curated list in fetcher.py.
- *Fix plan B (better):* News scraper targeting athlete investment announcements from Sportico, Boardroom, Front Office Sports.
- *Est. time plan A:* 30 min/quarter | *Plan B:* 4 hours to build

**[4] Rouzer returns only 1 signal**
- *Why:* David Rouzer mainly holds ETFs (not individual stocks) so Capitol Trades shows almost no individual equity trades.
- *Fix:* Replace Rouzer with the next-best politician by returns — Debbie Schultz (+142.3% in 2024, Capitol Trades ID: S001565) or Roger Williams (+111.2%, W000816).
- *Est. time:* 20 minutes

---

### BROKEN / NOT WORKING — Fix Next

**[5] Decisions reset on page reload**
- *Why:* `st.session_state` is in-memory only. Server restart or browser close wipes all approve/reject history.
- *Fix:* Write decisions to a local `decisions.json` file, load it on startup.
- *Est. time:* 30 minutes

**[6] No order confirmation visible**
- *Why:* Toast shows but there's no way to verify the Alpaca order actually went through without logging into Alpaca.
- *Fix:* After placing an order, query `client.get_order_by_id()` and display status (filled / pending / rejected) in the toast.
- *Est. time:* 30 minutes

**[7] No SELL signal support**
- *Why:* App is BUY-only. Politician sales are just as informative — Pelosi selling a stock before a crash is exactly what you want to know.
- *Fix:* Add SELL cards to the feed with a red accent. Add a SELL order path on Alpaca (only if position exists).
- *Est. time:* 2 hours

**[8] Stale `streamlit.log` contains old syntax error**
- *Why:* Leftover from the original broken app.py. Not a runtime issue but confusing if you check logs.
- *Fix:* Delete the file. Systemd journal is the correct log source now.
- *Est. time:* 2 minutes (done during cleanup)

---

### DATA QUALITY — Fix When Time Allows

**[9] No data freshness indicator in the UI**
- *Why:* No way to know when `suggestions.json` was last updated without SSH.
- *Fix:* Add `last_updated` timestamp to suggestions.json. Show "Updated X hours ago" at the top of the feed.
- *Est. time:* 30 minutes

**[10] Capitol Trades scraper is fragile**
- *Why:* Parses HTML with regex — any layout change silently breaks it and returns 0 signals.
- *Fix:* Add a health check after each fetch: if a politician returns 0 signals, write a warning to `fetcher.log` and send an email alert (use AWS SES free tier or a simple SMTP call).
- *Est. time:* 1 hour

**[11] CEO 13F data staleness not communicated**
- *Why:* Buffett's latest filing is Feb 2026, Burry's is Nov 2025. UI presents it alongside live politician data without distinguishing.
- *Fix:* Add a `data_as_of` field per suggestion, display it on the card as "Holdings as of Q4 2025".
- *Est. time:* 45 minutes

---

### MISSING FEATURES — Prioritise as You See Fit

**[12] Trade size is hardcoded at $500**
- *Why:* No UI control for trade size.
- *Fix:* Add a number input in a settings panel (or per-card slider). Store preference in session state / local JSON.
- *Est. time:* 45 minutes

**[13] Positions not tagged by originating category**
- *Why:* Alpaca positions show symbol/P&L but not whether a trade came from a politician signal or a CEO signal.
- *Fix:* Write a `trade_log.json` locally when an order is placed (ticker, category, investor, timestamp, notional). Show it alongside the Positions tab.
- *Est. time:* 1.5 hours

**[14] Leaderboard shows score only, not actual returns**
- *Why:* Score is a signal-strength proxy, not real money made.
- *Fix:* Cross-reference `trade_log.json` with Alpaca position P&L to compute actual return per category/investor.
- *Est. time:* 2 hours (depends on [13] being done first)

**[15] HTTPS and custom domain**
- *Why:* Raw EC2 IP over HTTP. Mobile browsers flag it as insecure; not suitable for daily use.
- *Fix options:*
  - Option A: Cloudflare Tunnel (free, no domain required — just a Cloudflare account).
  - Option B: Buy a domain (~$10/yr on Namecheap), point to EC2, add Let's Encrypt SSL via Caddy (1 hour setup).
- *Est. time plan A:* 45 minutes | *Plan B:* 1.5 hours

**[16] Dashboard never auto-refreshes**
- *Why:* Streamlit doesn't poll for new data. You have to manually click Refresh.
- *Fix:* Add `st.rerun()` on a timer using `time.sleep` inside a `st.empty()` fragment, or use `streamlit-autorefresh` component (pip install, 5 lines of code).
- *Est. time:* 20 minutes

---

### INFRASTRUCTURE — Plan Ahead

**[17] No monitoring or alerting**
- *Why:* If the service crashes or the cron fails, you won't know.
- *Fix:* Add a UptimeRobot free monitor on port 8501. Set up a 1-line cron health check that emails you if `fetcher.log` contains "ERROR".
- *Est. time:* 30 minutes

**[18] No backup of suggestions.json**
- *Why:* EC2 termination or disk failure loses all data.
- *Fix:* Add a post-fetch step in the cron that commits `suggestions.json` to git automatically, or copies it to S3 (AWS free tier: 5 GB).
- *Est. time:* 20 minutes

**[19] DynamoDB wired up but unused**
- *Why:* `database.py` exists, the Lambda references it, but nothing reads from or writes to it in the current app.
- *Decision needed:* Either wire DynamoDB as the persistence layer (replaces local JSON files) when going to production, or remove it until Lambda is deployed.
- *Est. time to wire up:* 2 hours | *Est. time to remove:* 5 minutes

**[20] Lambda never deployed**
- *Why:* `lambda_function.py` is code only — no AWS Lambda function exists, no CloudWatch trigger, no IAM role.
- *Plan:* Deploy when ready to move from manual-approve to fully automated trading. Uses dead S3 data sources — needs updating to Capitol Trades before deploy.
- *Est. time to deploy + update:* 3 hours

---

## Total Estimated Time

| Priority group | Items | Est. time |
|---|---|---|
| Critical | 1–4 | ~3 hours |
| Broken / not working | 5–8 | ~3 hours |
| Data quality | 9–11 | ~2.5 hours |
| Missing features | 12–16 | ~6.5 hours |
| Infrastructure | 17–20 | ~5.5 hours |
| **Total** | **20 items** | **~20 hours** |

---

## Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-04-26 | Dropped all investor/CEO/ARK/Musk categories from original app | App focus is politicians only for signal accuracy |
| 2026-04-26 | Added 4 categories (politicians, CEOs, athletes, sectors) | Diversify signal sources, richer feed |
| 2026-04-26 | Chose Capitol Trades HTML scraping over S3 feeds | Both S3 buckets dead since early 2026 (HTTP 403) |
| 2026-04-26 | Athletes use curated static lists | No public API or filing source exists for athlete trades |
| 2026-04-26 | Sectors use curated ETF top-holdings lists | ETFs don't file 13F themselves; fund manager CIKs don't match |
| 2026-04-26 | Kept Lambda code but not deployed | Useful future reference; deploy when moving to auto-trading |
| 2026-04-26 | Paper trading only until personal use proves profitable | No production until you see results with your own money |

---

## Open Questions — Answer When Ready

1. **Which politician replaces Rouzer?** Schultz (+142%) or Williams (+111%) are the best alternatives by 2024 returns.
2. **Athlete data refresh frequency?** Quarterly manual review is sufficient, or do you want a news scraper?
3. **Custom domain?** If yes, do you have a domain name in mind? Cloudflare Tunnel is zero-cost if not.
4. **Auto-trading timeline?** When do you want to move from manual-approve to Lambda executing trades automatically?
5. **Trade size?** Should it scale with account size (e.g. always 0.5% of equity) or stay fixed at $500?

---

*Add notes below any item as we discuss. Date your additions.*

Sunday April 4th 2026

1. add them both.
2. news scraper will meet my needs.
3. Cloudflare is fine with me.
4. Whenever I want. Should be able to switch between manual and automated trading.
5. Please scale with account size. No harcoded amount.
