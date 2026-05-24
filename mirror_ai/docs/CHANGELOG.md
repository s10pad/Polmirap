# CHANGELOG

This file is append-only. Entries are never edited or deleted. Every action the system takes — trades executed, trades vetoed, roster changes, errors, mode changes — is recorded here with a timestamp.

New entries are appended automatically by `memory.py` whenever `append_changelog()` is called. The dashboard LOGS tab reads from both Redis (for recent entries) and this file (as fallback).

---

## Entry format

```
[YYYY-MM-DD] ACTION SUBJECT — plain English explanation of what happened and why
```

Action types:
- `SYSTEM INIT` — application startup or initialization events
- `ROSTER ADD` — new member added to roster
- `ROSTER REMOVE` — member removed from roster
- `WEIGHT UPDATE` — member weight adjusted
- `DAILY_RUN` — daily analysis job ran
- `EXECUTED BUY` — trade executed on Alpaca
- `TRADE_QUEUED` — trade queued for retry (Alpaca unavailable)
- `SKIPPED` — trade vetoed by owner or blocked by rule
- `VETO` — owner explicitly vetoed a signal
- `APPROVED` — owner approved a signal
- `EXIT` — position closed (owner-initiated or stop loss)
- `HOLD` — owner dismissed stop loss alert
- `STOP_LOSS_ALERT` — stop loss threshold triggered, alert sent
- `WEEKLY_REVIEW` — weekly roster review proposal generated or applied
- `MODE CHANGE` — autonomy mode switched
- `ERROR` — any system error (API failure, parse error, etc.)

---

## Entries

[2026-05-21] SYSTEM INIT — MIRROR AI v2 project initialized.

[2026-05-24] MODE CHANGE — Switched to FULL via dashboard.
