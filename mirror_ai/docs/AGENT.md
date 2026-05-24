# AGENT.md — AI Autonomy Boundaries

This document defines what Mirror AI is allowed to do on its own, what requires owner input, and how it escalates when it cannot reach you.

---

## What the AI can do autonomously

The following actions happen without asking you first:

- **Fetch disclosures**: Every weekday at 7:30am ET, the system runs Brave Search queries for every roster member, looking for recent stock trade disclosures.
- **Parse trades**: Claude reads the raw search results and extracts structured trade events (ticker, buy/sell, estimated size, sector, date).
- **Score signals**: The scoring engine applies conviction multipliers and roster weights to produce a ranked list of buy signals.
- **Size positions**: Position sizes are calculated automatically using the conviction cap table and sector exposure rules defined in STRATEGY.md.
- **Send Telegram notifications**: Every signal above the threshold is sent to you with full details. Stop loss alerts are sent automatically when triggered.
- **Write to changelog**: Every action — fetches, scores, executions, alerts, errors — is appended to the changelog automatically.
- **Run weekly review**: Every Monday at 6am ET, the AI searches for news about roster members and potential replacements, generates a review proposal, and sends it to you. The proposal does not apply until you approve it.
- **Queue failed trades**: If Alpaca is unreachable when a trade should execute, the trade is queued in Redis for retry.

---

## What requires owner approval

The following actions **never happen without your explicit confirmation**:

- **Roster changes**: Adding, removing, or changing weights for roster members. The AI proposes these weekly but applies nothing until you reply `APPROVE` via Telegram or click "APPROVE ALL CHANGES" on the dashboard.
- **Strategy changes**: The conviction cap table, stop loss percentage, sector caps, and position sizing rules cannot be changed by the AI. They are set in environment variables and `strategy.py`. Changing them requires a code deployment.
- **Live trading activation**: Switching from paper to live trading requires changing `ALPACA_PAPER=false` in the environment and redeploying. The AI cannot change this.
- **Mode switching**: Switching between CONTROLLED and FULL autonomy requires explicit owner action — via Telegram command or dashboard toggle. There is a confirmation step on the dashboard.
- **Individual trade approval (FULL mode only exception)**: In FULL mode, trades with a score above 8.0 execute immediately. All other trades still go through the veto window even in FULL mode.

---

## Current mode: CONTROLLED

In CONTROLLED mode, the system operates as follows:

1. Signal detected → Telegram notification sent to owner
2. Owner has `VETO_WINDOW_HOURS` (default 2 hours) to reply `SKIP TICKER`
3. If no reply after the veto window → trade executes
4. If `SKIP TICKER` received → trade is blocked, logged, skipped forever for that day

This mode gives you full visibility and veto power over every trade.

---

## FULL autonomy mode — what changes

When you switch to FULL mode:

- Signals with a score >= 8.0 execute **immediately** after the daily analysis, with no Telegram notification first.
- Signals with a score below 8.0 still go through the normal veto window.
- You still receive Telegram confirmation after a trade executes.
- Roster changes still require your approval.
- Stop loss alerts still require your response.

The score threshold of 8.0 is high. It requires at least 3 people buying the same ticker, each with weight >= 1.0, with the full 1.5x conviction multiplier applied. Reaching this score without at least strong consensus is difficult by design.

To switch: send `SET MODE FULL` via Telegram or use the sidebar toggle in the dashboard. You will be asked to confirm.

---

## Telegram command reference

| Command | Mode | What it does |
|---|---|---|
| `SKIP TICKER` | Controlled + Full | Veto a pending trade signal. Blocks that ticker for 24 hours. |
| `APPROVE` | Both | Apply the current weekly roster review proposal. |
| `EXIT TICKER` | Both | Close an open Alpaca position. Logged to changelog. |
| `HOLD TICKER` | Both | Dismiss a stop loss alert for a position. Keeps it open. |
| `STATUS` | Both | Returns portfolio equity, buying power, mode, roster size. |
| `SET MODE FULL` | Controlled | Switch to full autonomy mode. |
| `SET MODE CONTROLLED` | Full | Switch back to controlled mode with veto window. |
| `HELP` | Both | Show the full command list in Telegram. |

---

## Escalation rules

The system cannot force you to respond. It escalates based on time without a reply.

### Trade signal escalation (CONTROLLED mode)
- **T+0**: Telegram notification sent with full signal details and veto instructions.
- **T+2h** (or `VETO_WINDOW_HOURS`): If no `SKIP` received, trade executes automatically. Execution confirmation sent.
- If Alpaca is unavailable at execution time: trade is queued in Redis. No automatic retry time — you must restart the app or trigger manually.

### Stop loss alert escalation
- **T+0**: Telegram alert sent with current price, entry price, drop percentage.
- **T+4h**: If no `EXIT` or `HOLD` received, a second alert is sent.
- No automatic exit is triggered. The system alerts only. You must reply `EXIT TICKER` to close the position.

### Weekly review escalation
- **Monday 6am**: Review proposal generated, Telegram notification sent.
- No expiry. Proposal stays in Redis until you `APPROVE` or `REJECT` it from the dashboard.
- If a new weekly review runs before the previous one is processed, the new proposal replaces the old one.

### Error escalation
- API failures (Alpaca, Claude, Brave, Redis) are logged to the changelog.
- Claude API failures during daily analysis mean no signals are generated for that day. No Telegram alert is sent for Claude failures — check the LOGS tab.
- Telegram send failures are logged to the changelog but cannot be surfaced via Telegram (obviously). Check the dashboard LOGS tab if you stop receiving messages.
