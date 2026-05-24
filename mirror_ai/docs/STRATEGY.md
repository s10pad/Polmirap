# STRATEGY.md — Trading Rules

Version: 1.0 | Last approved: 2026-05-21

This document is the authoritative rulebook for Mirror AI's trading decisions. All rules described here are implemented in `strategy.py`. Changes to this document must be accompanied by code changes and require owner approval — the AI cannot modify strategy rules autonomously.

---

## Conviction cap table

Position size is capped based on how many roster members are buying the same ticker at the same time. More people buying = more confidence = slightly larger allowed position.

| Number of buyers | Max position (% of portfolio) |
|---|---|
| 1 person | 1.0% |
| 2 people | 2.5% |
| 3 or more people | 5.0% |

These caps apply before the hard max and sector cap checks. The final position size is the minimum of all applicable limits.

The conviction cap is not a target — it is a ceiling. The actual position is typically smaller because it is also constrained by the estimated size of the disclosed trade (the "midpoint percentage" Claude estimates from the filing range).

---

## Hard position maximum

No single position may ever exceed `MAX_POSITION_PCT` of the portfolio. Default: **7%**.

This is an absolute hard cap that cannot be overridden by high conviction or score. It exists to prevent catastrophic concentration even if the entire roster agrees on a single ticker.

---

## Stop-loss rules

Mirror AI does not automatically exit positions. It alerts you and waits for your decision.

- **Threshold**: If a position drops `STOP_LOSS_PCT` (default: **15%**) from the entry price, a Telegram alert is sent.
- **Alert format**: Entry price, current price, percentage drop, and response instructions.
- **Response options**:
  - Reply `EXIT TICKER` → position is queued for market sell on Alpaca
  - Reply `HOLD TICKER` → alert is dismissed, no further alerts for 24 hours
  - No reply → second alert sent 4 hours later. No automatic exit.
- **Why no auto-exit**: Stop losses triggered by short-term volatility on fundamentally sound positions are often mistakes. You retain final authority on exits.

The stop loss check runs every hour on weekdays between 9am and 5pm ET.

---

## Sector concentration limits

The system tracks your portfolio's exposure to each market sector based on position metadata stored at trade entry time. Before sizing any new position, it checks whether adding the trade would push the sector above the cap.

- **Sector cap**: `SECTOR_CAP_PCT` (default: **20%**)
- If a new position would push the sector above 20%, the position is reduced to use only the available headroom.
- If the sector is already at or above 20%, the signal is discarded entirely for that day.
- The sector of each position is determined by Claude at signal time, stored in Redis, and used for all subsequent calculations.

**Example**: If Technology positions already make up 18% of your portfolio and a new NVDA signal would be 3% of portfolio, the position is reduced to 2% (the remaining headroom before the 20% cap).

---

## Confidence decay rates (weight adjustment)

Roster member weights are adjusted after each 30-day trade cycle completes.

| Outcome | Weight change |
|---|---|
| Profitable trade | +0.05 |
| Losing trade | -0.10 |

Losses penalize twice as much as wins reward. This is intentional: a person needs a 2:1 win/loss ratio to keep their weight stable. Consistent losers drift toward the minimum (0.5) quickly.

Weight bounds:
- **Minimum**: 0.5 (below this, someone should probably be removed)
- **Maximum**: 1.6 (trust ceiling to prevent any single person from dominating signals)

---

## Rebalancing rules

Mirror AI does not automatically rebalance. It adds positions when signals fire and alerts you when stop losses trigger. It does not:

- Automatically sell winning positions to take profits
- Automatically trim oversized positions due to price appreciation
- Rebalance sector allocations without a signal

If a position grows beyond its original allocation due to price appreciation, the sector cap calculation will reflect the larger position and reduce future allocations in that sector accordingly. This is passive rebalancing via new signal sizing, not active selling.

---

## How the AI resolves competing signals

On any given day, multiple signals may fire simultaneously. The scorer sorts them by score (descending) and sends them all as separate Telegram notifications. There is no automatic de-prioritization or mutual exclusion between signals.

However, the sector cap means that if two Technology signals fire on the same day:
- The first (higher score) signal is sized normally.
- The second signal's position is reduced by whatever the first signal consumed of the Technology allocation.
- If the first signal consumed the entire remaining Technology headroom, the second signal is discarded.

The ordering is deterministic: higher score = processed first = gets the headroom.

If two signals have the same score (unlikely but possible), they are processed in the order they appear in the scored list, which is alphabetical by ticker as a tiebreaker.

---

## Signal score threshold

- **Minimum to surface**: 0.5 (anything below is discarded silently)
- **FULL mode auto-execution threshold**: 8.0 (only applies when AUTONOMY_MODE=full)

The 0.5 threshold filters out noise — a single low-weight person buying a stock you already hold in the sector-capped area would score below 0.5 and not be surfaced at all.

The 8.0 FULL mode threshold is very high by design. Reaching it requires consensus from multiple high-weight roster members buying the same ticker. It is intended to capture only the strongest "everyone agrees" scenarios for autonomous execution.

---

## Approval requirement

This strategy document cannot be changed by the AI. Any modification to the rules in this file requires:

1. Owner edits to `strategy.py` (or environment variables for configurable limits)
2. A new deployment
3. An entry in CHANGELOG.md noting the change and the date it was approved

The AI may recommend strategy changes in the weekly review summary text, but it cannot apply them. Recommendations appear in the review proposal's `summary` field. Acting on them is always the owner's decision.
