# MIRROR AI — Improvement Discussion

This is a living document for us to track and debate improvements to the app — technical, visual, and revenue-generating.
Add comments, priority rankings, and decisions as we talk.

---

## Current limitations (what's not working yet)

| # | Issue | File | Impact |
|---|---|---|---|
| 1 | `suggestions.json` path is hardcoded to `/home/ubuntu/` — breaks on Windows/local | `app.py`, `scorer.py` | App won't load locally |
| 2 | `lambda_function.py` has an empty `targets = ` list — Lambda does nothing | `lambda_function.py` | No automated trades |
| 3 | `strategy.py` has a bug: `parts[3]` should be `parts[1]` in amount parsing | `strategy.py` | Position sizing always returns 0 |
| 4 | Pelosi scraper relies on static regex of hardcoded tickers — misses most real trades | `fetcher.py` | Low data quality |
| 5 | Musk Form 4 data is fetched but never used in scoring | `fetcher.py`, `scorer.py` | Dead feature |
| 6 | No scheduler — `fetcher.py` + `scorer.py` must be run manually | — | Data goes stale |
| 7 | App shows "7 investors" in subtitle but only 4 are fully wired | `app.py` | Misleading |
| 8 | `conviction` count in `suggestions.json` is always 1 for most stocks (deduplication issue) | `scorer.py` | Scores are inaccurate |

---

## Technical improvements

### High priority

- **Fix the hardcoded paths** — replace `/home/ubuntu/` with `pathlib.Path(__file__).parent` so the app runs anywhere
- **Fix the `parts[3]` bug** in `strategy.py` — `parts[1]` is the upper bound of the range
- **Wire the Lambda targets list** — add the top 7 politicians (Pelosi, Tuberville, Collins, Jeffries, etc.)
- **Add a scheduler** — either a cron job (Linux/EC2), Windows Task Scheduler, or APScheduler inside the app to refresh data daily before market open
- **De-duplicate APPLE INC vs APPLE** properly in scorer — currently the same company appears multiple times under different names, inflating/splitting scores
- **Expose `suggestions.json` path as a config** — env var or a `config.py` so it's not hardcoded

### Medium priority

- **Real-time price data** — integrate a free market data API (Alpaca data API, Yahoo Finance via `yfinance`) to show current price, day change % on each card
- **Sell signals** — the feed only shows BUY. Add SELL signals when a politician files a sale disclosure or exits a position in a 13F
- **Historical score chart** — track suggestion scores over time so you can see trends (is Buffett accumulating AAPL again?)
- **Ticker symbol resolution** — map company names to actual tickers using a lookup table or the Alpaca assets API, rather than slicing `name.split()[0][:5]` (currently broken for multi-word names)
- **DynamoDB optional** — make it a graceful fallback; currently boto3 import failure can crash the scorer
- **Unit tests** — scorer logic and strategy sizing have bugs that tests would have caught

### Lower priority

- **PWA / mobile install** — `manifest.json` is already there, just needs a favicon and service worker to be installable on iOS/Android
- **Alpaca OAuth** — let other users connect their own Alpaca accounts via OAuth instead of pasting keys into env vars
- **Multiple portfolio sizes** — currently hardcoded to $500 per trade; let users set their own trade size
- **Export to CSV** — one-click download of the suggestion log for tax/record-keeping

---

## Visual improvements

### High priority

- **Ticker symbol on cards** — the card shows the full company name but you have to guess the ticker; show it prominently
- **Price + day change** — each card should show current price and % change today (the single most important missing data point)
- **Mobile layout** — `max-width: 480px` is set but the columns (`st.columns`) break on small screens; replace with stacked layout on mobile

### Medium priority

- **Dark-mode chart for positions** — a simple sparkline of each position's price history would add a lot without much complexity
- **Conviction bar colours** — green for high conviction (5-7 investors), amber for medium (3-4), red for low (1-2); currently always green
- **Animated approval** — a subtle swipe/fade when you approve/reject a card (CSS transition) makes the interaction feel intentional
- **News feed per stock** — show 1-2 recent headlines per suggestion (via NewsAPI or Alpaca news) so you can make an informed decision
- **Investor avatars** — small circular icons or initials chips for each investor instead of plain text pills

### Lower priority

- **Theming** — allow switching between dark (current) and light modes
- **Onboarding screen** — a brief explainer for new users so they understand what "conviction 6/7" means before they start tapping APPROVE

---

## Monetisation ideas

These are ranked by effort vs. revenue potential:

| Rank | Idea | Effort | Revenue model |
|---|---|---|---|
| 1 | **Subscription SaaS** | Medium | $15–$49/mo for real-time signals, auto-execute, and portfolio analytics |
| 2 | **Auto-execute tier** — pay for the Lambda to trade for you automatically | Low (Lambda already exists) | Premium subscription add-on |
| 3 | **Referral / affiliate links to Alpaca** — Alpaca pays ~$50–$100 per funded account referral | Very low | Passive |
| 4 | **Copy-trade marketplace** — users publish their own "politician portfolios"; followers pay to mirror | High | Rev-share or subscription |
| 5 | **Data API** — sell the scored signal feed as a JSON/webhook API to other devs/apps | Medium | API key tiers ($0 / $29 / $99/mo) |
| 6 | **White-label** — sell the whole stack to a hedge fund or fintech as a private label | High | Enterprise licensing |
| 7 | **Sponsored signals** — broker-dealers pay to feature their research alongside politician signals | Low | CPM / flat fee |

### Fastest path to money
1. Fix the bugs so the app actually works end-to-end
2. Deploy on a real domain (Railway, Render, or EC2 already configured)
3. Add Stripe + user auth (Supabase Auth or Clerk) with a 7-day free trial
4. Launch as a $15/mo subscription — "Mirror what Congress buys, automatically"
5. Affiliate links to Alpaca on every page → passive income from day one

---

## Questions for discussion

- Which politicians should be the initial target list? (Pelosi, Tuberville, Collins are the most traded — which 7?)
- Should auto-execute be on by default (with a daily limit) or always require manual approval?
- Do you want this deployed on the existing EC2 (`18.234.219.234`) or move to a managed platform?
- Should the scoring also track SELL disclosures and generate SHORT signals, or stay BUY-only for now?
- Is the end goal a personal trading tool, or a product you sell to others?

---

*Last updated: 2026-04-26 — add your answers/comments below each question as we talk*
