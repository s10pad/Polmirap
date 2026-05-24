"""
Firestore state layer — all persistent data flows through here.
Uses Firebase Admin SDK. Every collection is under the 'state' collection.
Credentials: FIREBASE_CREDENTIALS_PATH (file) or FIREBASE_CREDENTIALS_JSON (env string).
"""

import os
import json
import logging
from datetime import datetime
from typing import Any, Optional

import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

_db = None
_DOC_PREFIX = "state"


def get_db():
    """Return a singleton Firestore client, initializing Firebase on first call."""
    global _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:
        cred_json_str = os.getenv("FIREBASE_CREDENTIALS_JSON")
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")

        if cred_json_str:
            cred = credentials.Certificate(json.loads(cred_json_str))
        else:
            cred = credentials.Certificate(cred_path)

        firebase_admin.initialize_app(cred, {
            "projectId": os.getenv("FIREBASE_PROJECT_ID", "polmirap-25a9a"),
        })

    _db = firestore.client()
    return _db


def _doc_ref(key: str):
    """Return a Firestore document reference for the given key."""
    return get_db().collection(_DOC_PREFIX).document(key)


def set_key(key: str, value: Any) -> bool:
    """Write a value to Firestore. Stores dicts/lists directly; wraps scalars in {data: value}."""
    try:
        ref = _doc_ref(key)
        if isinstance(value, (dict, list)):
            ref.set({"data": value})
        else:
            ref.set({"data": value})
        return True
    except Exception as e:
        logger.error(f"Firestore set failed for key {key}: {e}")
        return False


def get_key(key: str, default: Any = None) -> Any:
    """Read a value from Firestore. Returns default if document missing."""
    try:
        doc = _doc_ref(key).get()
        if not doc.exists:
            return default
        data = doc.to_dict()
        return data.get("data", default)
    except Exception as e:
        logger.error(f"Firestore get failed for key {key}: {e}")
        return default


def delete_key(key: str) -> bool:
    """Delete a document from Firestore."""
    try:
        _doc_ref(key).delete()
        return True
    except Exception as e:
        logger.error(f"Firestore delete failed for key {key}: {e}")
        return False


def get_roster() -> list:
    """Return the current roster list. Empty list if not initialized."""
    return get_key("roster", [])


def set_roster(roster: list) -> bool:
    """Persist the full roster list."""
    return set_key("roster", roster)


def get_autonomy_mode() -> str:
    """Return current autonomy mode: 'controlled' or 'full'."""
    return get_key("autonomy_mode", os.getenv("AUTONOMY_MODE", "controlled"))


def set_autonomy_mode(mode: str) -> bool:
    """Set autonomy mode. Only accepts 'controlled' or 'full'."""
    if mode not in ("controlled", "full"):
        logger.error(f"Invalid autonomy mode: {mode}")
        return False
    return set_key("autonomy_mode", mode)


def get_pending_signals() -> list:
    """Return all signals waiting for owner veto decision."""
    return get_key("pending_signals", [])


def set_pending_signals(signals: list) -> bool:
    """Persist the pending signals list."""
    return set_key("pending_signals", signals)


def get_vetoed_tickers() -> list:
    """Return list of tickers the owner has vetoed today."""
    return get_key("vetoed_tickers", [])


def add_vetoed_ticker(ticker: str) -> bool:
    """Mark a ticker as vetoed. Resets on next daily run (scheduler clears stale vetoes)."""
    vetoed = get_vetoed_tickers()
    if ticker not in vetoed:
        vetoed.append(ticker)
    return set_key("vetoed_tickers", vetoed)


def get_trade_queue() -> list:
    """Return trades queued for retry (e.g. Alpaca was unreachable)."""
    return get_key("trade_queue", [])


def set_trade_queue(queue: list) -> bool:
    """Persist the trade retry queue."""
    return set_key("trade_queue", queue)


def get_open_positions_meta() -> dict:
    """Return metadata about open positions (who triggered, entry date)."""
    return get_key("positions_meta", {})


def set_open_positions_meta(meta: dict) -> bool:
    """Persist position metadata."""
    return set_key("positions_meta", meta)


def append_changelog(entry: str) -> bool:
    """Append a plain-English entry to the changelog in Firestore and the MD file."""
    try:
        log = get_key("changelog", [])
        log.append(entry)
        set_key("changelog", log)
        _append_to_changelog_file(entry)
        return True
    except Exception as e:
        logger.error(f"Changelog append failed: {e}")
        return False


def _append_to_changelog_file(entry: str):
    """Write a changelog entry to docs/CHANGELOG.md on disk."""
    changelog_path = os.path.join(os.path.dirname(__file__), "docs", "CHANGELOG.md")
    try:
        with open(changelog_path, "a", encoding="utf-8") as f:
            f.write(f"\n{entry}\n")
    except Exception as e:
        logger.error(f"Could not write to CHANGELOG.md: {e}")


def get_changelog() -> list:
    """Return all changelog entries."""
    return get_key("changelog", [])


def get_review_proposal() -> Optional[dict]:
    """Return the current pending weekly review proposal."""
    return get_key("review_proposal")


def set_review_proposal(proposal: dict) -> bool:
    """Store a weekly review proposal awaiting owner approval."""
    return set_key("review_proposal", proposal)


def clear_review_proposal() -> bool:
    """Clear the review proposal after it's been processed."""
    return delete_key("review_proposal")


def get_last_roster_boot() -> Optional[str]:
    """Return the timestamp of the last roster initialization."""
    return get_key("last_roster_boot")


def set_last_roster_boot(ts: str) -> bool:
    """Record when the roster was last initialized."""
    return set_key("last_roster_boot", ts)


def is_roster_initialized() -> bool:
    """Check if the roster has been bootstrapped at least once."""
    return len(get_roster()) > 0


def get_member_performance(name: str) -> float:
    """Return the cumulative P&L % for a roster member's mirrored trades."""
    perf = get_key("member_performance", {})
    return perf.get(name, 0.0)


def update_member_performance(name: str, delta_pct: float) -> bool:
    """Add delta_pct to a member's running performance total."""
    perf = get_key("member_performance", {})
    perf[name] = round(perf.get(name, 0.0) + delta_pct, 4)
    return set_key("member_performance", perf)


def get_watchlist() -> list:
    """Return the owner's manually curated watchlist of tickers."""
    return get_key("watchlist", [])


def add_to_watchlist(ticker: str) -> bool:
    """Add a ticker to the watchlist. Idempotent — duplicates ignored."""
    tickers = get_watchlist()
    ticker = ticker.upper()
    if ticker not in tickers:
        tickers.append(ticker)
        return set_key("watchlist", tickers)
    return True


def remove_from_watchlist(ticker: str) -> bool:
    """Remove a ticker from the watchlist."""
    tickers = get_watchlist()
    ticker = ticker.upper()
    if ticker in tickers:
        tickers.remove(ticker)
        return set_key("watchlist", tickers)
    return True
