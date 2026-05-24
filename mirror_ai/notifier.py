"""
Telegram notification and veto system.
Sends trade signals, receives SKIP/APPROVE/EXIT/HOLD commands from owner.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from memory import (
    append_changelog, add_vetoed_ticker, get_pending_signals,
    set_pending_signals, get_autonomy_mode,
)
from strategy import TradeProposal

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


async def send_message(text: str) -> bool:
    """Send a Telegram message to the owner chat. Returns True on success."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("Telegram not configured — message not sent")
        return False
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] ERROR TELEGRAM — Send failed: {e}"
        )
        return False


def send_signal_notification(proposal: TradeProposal, equity: float) -> None:
    """Send a trade signal to the owner with conviction details and veto instructions."""
    buyers_text = "\n".join(
        f"  • {b['name']} ({b['portfolio_pct']:.1f}% of their portfolio)"
        for b in proposal.buyers
    )
    veto_hours = int(os.getenv("VETO_WINDOW_HOURS", "2"))
    msg = (
        f"🟢 <b>MIRROR SIGNAL — BUY ${proposal.ticker}</b>\n"
        f"Conviction: {proposal.conviction}/10 people | Score: {proposal.score:.2f}\n\n"
        f"Buyers:\n{buyers_text}\n\n"
        f"Trade size: <b>{proposal.position_pct:.1f}% of your account (~${proposal.position_usd:,.0f})</b>\n\n"
        f"Reasoning: {proposal.reasoning}\n\n"
        f"⏱ You have <b>{veto_hours} hours</b> to veto.\n"
        f"Reply <b>SKIP {proposal.ticker}</b> to block.\n"
        f"No reply = trade executes automatically."
    )
    asyncio.run(send_message(msg))


def send_execution_confirmation(ticker: str, price: float, shares: float) -> None:
    """Notify owner that a trade was executed."""
    msg = (
        f"✅ <b>EXECUTED — Bought ${ticker}</b>\n"
        f"Price: ${price:.2f} | Shares: {shares:.4f}\n"
        f"Position logged. Reasoning saved to CHANGELOG."
    )
    asyncio.run(send_message(msg))


def send_skip_confirmation(ticker: str) -> None:
    """Notify owner that a trade was skipped by their veto."""
    msg = (
        f"⏭️ <b>SKIPPED — ${ticker} trade blocked by owner.</b>\n"
        f"Logged to CHANGELOG."
    )
    asyncio.run(send_message(msg))


def send_stop_loss_alert(ticker: str, entry_price: float, current_price: float) -> None:
    """Alert owner to a position that has hit the stop loss threshold."""
    drop_pct = ((entry_price - current_price) / entry_price) * 100
    stop_pct = float(os.getenv("STOP_LOSS_PCT", "15"))
    msg = (
        f"⚠️ <b>STOP LOSS ALERT — ${ticker} is down {drop_pct:.1f}%</b>\n"
        f"Entry: ${entry_price:.2f} | Current: ${current_price:.2f}\n"
        f"Threshold: {stop_pct}%\n\n"
        f"Reply <b>EXIT {ticker}</b> to sell or <b>HOLD {ticker}</b> to keep.\n"
        f"If no reply in 4 hours, a second alert will be sent."
    )
    asyncio.run(send_message(msg))


def send_weekly_review_notification(proposal: dict) -> None:
    """Tell owner a weekly roster review proposal is ready."""
    changes = proposal.get("changes", [])
    n_changes = len([c for c in changes if c.get("action") != "keep"])
    msg = (
        f"📋 <b>WEEKLY ROSTER REVIEW — {n_changes} change(s) proposed</b>\n\n"
        f"{proposal.get('summary', '')}\n\n"
        f"Reply <b>APPROVE</b> to apply all changes,\n"
        f"or open the dashboard to review individually."
    )
    asyncio.run(send_message(msg))


def send_status_report(account_info: dict, roster: list) -> None:
    """Send a STATUS summary to the owner on request."""
    mode = get_autonomy_mode()
    msg = (
        f"📊 <b>MIRROR AI STATUS</b>\n\n"
        f"Mode: <b>{mode.upper()}</b>\n"
        f"Portfolio equity: <b>${account_info.get('equity', 0):,.2f}</b>\n"
        f"Buying power: ${account_info.get('buying_power', 0):,.2f}\n"
        f"Roster size: {len(roster)} members\n\n"
        f"Reply HELP for command list."
    )
    asyncio.run(send_message(msg))


def handle_telegram_command(text: str) -> Optional[str]:
    """
    Process incoming Telegram commands from the owner.
    Returns a response string or None.
    Supports: SKIP <TICKER>, APPROVE, EXIT <TICKER>, HOLD <TICKER>, STATUS, SET MODE <mode>.
    """
    from memory import set_autonomy_mode, get_review_proposal
    from roster import apply_review_proposal

    text = text.strip().upper()

    if text.startswith("SKIP "):
        ticker = text[5:].strip()
        add_vetoed_ticker(ticker)
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] VETO {ticker} — Owner vetoed via Telegram."
        )
        return f"⏭️ ${ticker} blocked. Will not execute."

    if text == "APPROVE":
        proposal = get_review_proposal()
        if not proposal:
            return "No pending review proposal."
        n, actions = apply_review_proposal(proposal)
        summary = "\n".join(f"• {a}" for a in actions)
        return f"✅ {n} roster change(s) applied:\n{summary}"

    if text.startswith("EXIT "):
        ticker = text[5:].strip()
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] EXIT {ticker} — Owner ordered exit via Telegram."
        )
        return f"🔴 Exit order logged for ${ticker}. Processing..."

    if text.startswith("HOLD "):
        ticker = text[5:].strip()
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] HOLD {ticker} — Owner chose to hold via Telegram."
        )
        return f"🟡 ${ticker} marked HOLD. No stop loss exit."

    if text == "STATUS":
        return None  # handled by caller with full account data

    if text == "SET MODE FULL":
        set_autonomy_mode("full")
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] MODE CHANGE — Switched to FULL autonomy via Telegram."
        )
        return "⚡ Autonomy mode set to FULL. Trades will execute immediately on high-confidence signals."

    if text == "SET MODE CONTROLLED":
        set_autonomy_mode("controlled")
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] MODE CHANGE — Switched to CONTROLLED mode via Telegram."
        )
        return "🔒 Autonomy mode set to CONTROLLED. 2-hour veto window restored."

    if text == "HELP":
        return (
            "📖 <b>Commands:</b>\n"
            "SKIP TICKER — veto a trade\n"
            "APPROVE — apply roster review\n"
            "EXIT TICKER — sell a position\n"
            "HOLD TICKER — keep despite stop loss\n"
            "STATUS — account + roster summary\n"
            "SET MODE FULL — enable full autonomy\n"
            "SET MODE CONTROLLED — enable veto window"
        )

    return None
