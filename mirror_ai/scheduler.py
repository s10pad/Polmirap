"""
APScheduler job definitions — daily trade loop and weekly roster review.
Runs as a background service alongside the Streamlit dashboard.
"""

import os
import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler = None


def run_daily_job():
    """
    Weekday morning job: fetch disclosures, score signals, send Telegram notifications.
    Queues approved trades for execution after the veto window.
    """
    from agent import run_daily_analysis
    from roster_discovery import discover_and_refresh_roster
    from memory import (
        is_roster_initialized, get_pending_signals, set_pending_signals,
        get_vetoed_tickers, append_changelog, get_autonomy_mode,
    )
    from notifier import send_signal_notification
    from strategy import TradeProposal, FULL_MODE_AUTO_THRESHOLD
    import json

    logger.info("Daily job started")

    # Bootstrap roster on first run via discovery engine
    if not is_roster_initialized():
        logger.info("First run detected — bootstrapping roster via AI discovery")
        discover_and_refresh_roster()
        _update_memory_md()

    proposals = run_daily_analysis()
    if not proposals:
        logger.info("No signals today")
        return

    pending = get_pending_signals()
    vetoed = get_vetoed_tickers()

    try:
        from alpaca.trading.client import TradingClient
        alpaca = TradingClient(
            os.getenv("ALPACA_KEY", ""),
            os.getenv("ALPACA_SECRET", ""),
            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true",
        )
        account = alpaca.get_account()
        equity = float(account.equity)
    except Exception as e:
        logger.error(f"Could not fetch Alpaca equity: {e}")
        equity = 0.0

    for proposal in proposals:
        if proposal.ticker in vetoed:
            logger.info(f"Skipping vetoed ticker {proposal.ticker}")
            continue

        mode = get_autonomy_mode()
        if mode == "full" and proposal.score >= FULL_MODE_AUTO_THRESHOLD:
            _execute_trade(proposal)
        else:
            send_signal_notification(proposal, equity)
            pending.append({
                "signal_id": proposal.signal_id,
                "ticker": proposal.ticker,
                "action": proposal.action,
                "score": proposal.score,
                "conviction": proposal.conviction,
                "buyers": proposal.buyers,
                "position_pct": proposal.position_pct,
                "position_usd": proposal.position_usd,
                "sector": proposal.sector,
                "reasoning": proposal.reasoning,
                "queued_at": datetime.now().isoformat(),
                "status": "pending",
            })

    set_pending_signals(pending)
    logger.info(f"Daily job complete — {len(proposals)} signals queued")


def run_veto_window_check():
    """
    Runs 2+ hours after daily job — executes any signals that were not vetoed.
    Skips signals with status 'vetoed'.
    """
    from memory import get_pending_signals, set_pending_signals, get_vetoed_tickers, append_changelog
    from notifier import send_skip_confirmation
    import os
    from datetime import datetime, timedelta

    pending = get_pending_signals()
    vetoed = get_vetoed_tickers()
    veto_hours = int(os.getenv("VETO_WINDOW_HOURS", "2"))

    still_pending = []
    for signal in pending:
        if signal.get("status") != "pending":
            continue
        queued_at = datetime.fromisoformat(signal["queued_at"])
        if datetime.now() - queued_at < timedelta(hours=veto_hours):
            still_pending.append(signal)
            continue
        if signal["ticker"] in vetoed:
            send_skip_confirmation(signal["ticker"])
            append_changelog(
                f"[{datetime.now().strftime('%Y-%m-%d')}] SKIPPED {signal['ticker']} — Vetoed by owner."
            )
        else:
            from strategy import TradeProposal
            proposal = TradeProposal(
                ticker=signal["ticker"],
                action=signal["action"],
                score=signal["score"],
                conviction=signal["conviction"],
                buyers=signal["buyers"],
                position_pct=signal["position_pct"],
                position_usd=signal["position_usd"],
                sector=signal["sector"],
                reasoning=signal["reasoning"],
                signal_id=signal["signal_id"],
            )
            _execute_trade(proposal)

    set_pending_signals(still_pending)


def run_weekly_review_job():
    """
    Monday morning job: generate watch report, auto-apply changes, notify via Telegram.
    """
    from watch_report import generate_and_apply_watch_report
    from notifier import send_weekly_review_notification
    from memory import append_changelog

    logger.info("Weekly review job started")
    report = generate_and_apply_watch_report()
    if report:
        proposal = {"summary": report["summary"], "changes": report["changes_proposed"]}
        try:
            send_weekly_review_notification(proposal)
        except Exception as e:
            logger.error(f"Weekly review notification failed: {e}")
        _update_memory_md()
    else:
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] WEEKLY_REVIEW — Review generation failed."
        )


def run_roster_discovery_job():
    """Sunday midnight job: refresh the full roster via AI discovery across all sources."""
    from roster_discovery import discover_and_refresh_roster
    logger.info("Roster discovery job started")
    count, changes = discover_and_refresh_roster()
    _update_memory_md()
    logger.info(f"Roster discovery complete: {count} change(s)")


def run_stop_loss_check():
    """
    Runs every hour — checks all open positions against the stop loss threshold.
    Sends alert if any position is down more than STOP_LOSS_PCT.
    """
    from fetcher import get_current_price
    from memory import get_open_positions_meta, append_changelog
    from notifier import send_stop_loss_alert
    from strategy import is_stop_loss_triggered
    import os

    try:
        from alpaca.trading.client import TradingClient
        alpaca = TradingClient(
            os.getenv("ALPACA_KEY", ""),
            os.getenv("ALPACA_SECRET", ""),
            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true",
        )
        positions = alpaca.get_all_positions()
    except Exception as e:
        logger.error(f"Stop loss check — Alpaca unavailable: {e}")
        return

    meta = get_open_positions_meta()
    for pos in positions:
        entry_price = float(meta.get(pos.symbol, {}).get("entry_price", pos.avg_entry_price or 0))
        current_price = float(pos.current_price or 0)
        if entry_price > 0 and is_stop_loss_triggered(entry_price, current_price):
            send_stop_loss_alert(pos.symbol, entry_price, current_price)
            append_changelog(
                f"[{datetime.now().strftime('%Y-%m-%d')}] STOP_LOSS_ALERT {pos.symbol} — "
                f"Down from ${entry_price:.2f} to ${current_price:.2f}. Alert sent to owner."
            )


def _execute_trade(proposal):
    """Execute a single trade proposal on Alpaca. Queues on failure."""
    from memory import (
        append_changelog, get_open_positions_meta, set_open_positions_meta,
        get_trade_queue, set_trade_queue,
    )
    from notifier import send_execution_confirmation
    import os
    from datetime import datetime

    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        alpaca = TradingClient(
            os.getenv("ALPACA_KEY", ""),
            os.getenv("ALPACA_SECRET", ""),
            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true",
        )
        order = alpaca.submit_order(
            MarketOrderRequest(
                symbol=proposal.ticker,
                notional=proposal.position_usd,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )
        )

        # Store position metadata
        meta = get_open_positions_meta()
        meta[proposal.ticker] = {
            "entry_date": datetime.now().strftime("%Y-%m-%d"),
            "entry_price": float(order.filled_avg_price or 0),
            "triggered_by": [b["name"] for b in proposal.buyers],
            "signal_id": proposal.signal_id,
            "sector": proposal.sector,
        }
        set_open_positions_meta(meta)

        send_execution_confirmation(
            proposal.ticker,
            float(order.filled_avg_price or 0),
            float(order.filled_qty or 0),
        )
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] EXECUTED BUY {proposal.ticker} — "
            f"${proposal.position_usd:.2f} ({proposal.position_pct:.1f}% of portfolio). "
            f"Conviction: {proposal.conviction}. Score: {proposal.score:.2f}. "
            f"Reason: {proposal.reasoning}"
        )

    except Exception as e:
        logger.error(f"Trade execution failed for {proposal.ticker}: {e}")
        queue = get_trade_queue()
        queue.append({
            "ticker": proposal.ticker,
            "position_usd": proposal.position_usd,
            "queued_at": datetime.now().isoformat(),
            "error": str(e),
        })
        set_trade_queue(queue)
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] TRADE_QUEUED {proposal.ticker} — "
            f"Alpaca unavailable. Queued for retry. Error: {e}"
        )


def _update_memory_md():
    """Rewrite docs/MEMORY.md with current roster state in plain English."""
    from memory import get_roster
    import os
    from datetime import datetime

    roster = get_roster()
    lines = [
        "# MEMORY — Current Roster",
        f"\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n",
        "This file is auto-generated. It records who is on the Mirror AI roster, why they're here,",
        "and how they've performed.\n",
        "---\n",
        "## Active Members\n",
    ]
    for i, m in enumerate(roster, 1):
        lines += [
            f"### {i}. {m['name']}",
            f"- **Category:** {m.get('category', 'unknown')}",
            f"- **Why added:** {m.get('why_added', 'N/A')}",
            f"- **Weight:** {m.get('weight', 1.0):.2f} (higher = more trusted)",
            f"- **Performance since added:** {m.get('performance_since_added', 0.0):.1f}%",
            f"- **Added:** {m.get('added_date', 'unknown')}",
            f"- **Last reviewed:** {m.get('last_reviewed', 'never')}",
            "",
        ]

    lines += [
        "---\n",
        "## Pending Proposals\n",
        "*(None — check the dashboard for live proposals)*\n",
    ]

    path = os.path.join(os.path.dirname(__file__), "docs", "MEMORY.md")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception as e:
        logger.error(f"Could not write MEMORY.md: {e}")


def start_scheduler():
    """Initialize and start the background scheduler with all jobs."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="America/New_York")

    # Daily analysis: weekdays at 7:30am ET
    _scheduler.add_job(
        run_daily_job,
        CronTrigger(day_of_week="mon-fri", hour=7, minute=30),
        id="daily_analysis",
        replace_existing=True,
    )

    # Veto window check: weekdays at 9:45am ET (after 2h veto window)
    _scheduler.add_job(
        run_veto_window_check,
        CronTrigger(day_of_week="mon-fri", hour=9, minute=45),
        id="veto_check",
        replace_existing=True,
    )

    # Weekly roster review: Mondays at 6am ET
    _scheduler.add_job(
        run_weekly_review_job,
        CronTrigger(day_of_week="mon", hour=6, minute=0),
        id="weekly_review",
        replace_existing=True,
    )

    # Stop loss check: every hour during market hours (9am-5pm ET weekdays)
    _scheduler.add_job(
        run_stop_loss_check,
        CronTrigger(day_of_week="mon-fri", hour="9-17", minute=0),
        id="stop_loss_check",
        replace_existing=True,
    )

    # Weekly roster discovery: Sundays at midnight ET
    _scheduler.add_job(
        run_roster_discovery_job,
        CronTrigger(day_of_week="sun", hour=0, minute=0),
        id="roster_discovery",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Scheduler started — daily 7:30am ET, weekly Monday 6am ET")
    return _scheduler


def stop_scheduler():
    """Gracefully stop the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        logger.info("Scheduler stopped")
