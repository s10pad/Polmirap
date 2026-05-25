"""
FastAPI application — headless JSON API for MIRROR AI.
All secrets live server-side. Browser never touches credentials.
Firebase ID-token authentication required on all /api/* endpoints.

Set DEV_MODE=true to skip Firebase auth for local development without credentials.
Start: uvicorn api:app --reload --port 8000
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DEV_MODE:
        from memory import get_db
        from scheduler import start_scheduler
        get_db()
        start_scheduler()
    logger.info("MIRROR AI API started%s", " (DEV MODE)" if DEV_MODE else "")
    yield
    if not DEV_MODE:
        from scheduler import stop_scheduler
        stop_scheduler()
    logger.info("MIRROR AI API shut down")


app = FastAPI(title="MIRROR AI API", version="2.0.0", lifespan=lifespan)

_cors_origins = ["http://localhost:3000", "http://localhost:3001"]
if os.getenv("FRONTEND_URL"):
    _cors_origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


async def get_current_uid(authorization: str = Header(default=None)) -> str:
    """Verify Firebase ID token → uid. DEV_MODE always returns 'dev-user'."""
    if DEV_MODE:
        return os.getenv("DEV_UID", "dev-user")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        from firebase_admin import auth as fb_auth
        decoded = fb_auth.verify_id_token(token)
        return decoded["uid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "dev_mode": DEV_MODE}


# ── Roster ────────────────────────────────────────────────────────────────────

@app.get("/api/roster")
async def get_roster_endpoint(uid: str = Depends(get_current_uid)):
    from memory import get_roster
    roster = [m for m in get_roster() if m.get("status") == "active"]
    return {"roster": roster, "count": len(roster)}


@app.post("/api/roster/refresh")
async def refresh_roster(uid: str = Depends(get_current_uid)):
    """Trigger a manual roster discovery run."""
    from roster_discovery import discover_and_refresh_roster
    count, changes = discover_and_refresh_roster()
    return {"changes_applied": count, "changes": changes}


# ── Signals ───────────────────────────────────────────────────────────────────

@app.get("/api/signals")
async def get_signals(uid: str = Depends(get_current_uid)):
    from memory import get_pending_signals
    signals = [s for s in get_pending_signals() if s.get("status") == "pending"]
    return {"signals": signals, "count": len(signals)}


@app.post("/api/signals/{signal_id}/approve")
async def approve_signal(signal_id: str, uid: str = Depends(get_current_uid)):
    from memory import get_pending_signals, set_pending_signals, append_changelog
    signals = get_pending_signals()
    for s in signals:
        if s.get("signal_id") == signal_id:
            s["status"] = "approved"
            set_pending_signals(signals)
            append_changelog(f"Signal {signal_id} approved via API.")
            return {"status": "approved", "signal_id": signal_id}
    raise HTTPException(status_code=404, detail="Signal not found")


@app.post("/api/signals/{signal_id}/reject")
async def reject_signal(signal_id: str, uid: str = Depends(get_current_uid)):
    from memory import get_pending_signals, set_pending_signals, add_vetoed_ticker, append_changelog
    signals = get_pending_signals()
    for s in signals:
        if s.get("signal_id") == signal_id:
            s["status"] = "vetoed"
            add_vetoed_ticker(s["ticker"])
            set_pending_signals(signals)
            append_changelog(f"Signal {signal_id} rejected, {s['ticker']} vetoed via API.")
            return {"status": "vetoed", "signal_id": signal_id, "ticker": s["ticker"]}
    raise HTTPException(status_code=404, detail="Signal not found")


# ── Positions & Account ───────────────────────────────────────────────────────

@app.get("/api/positions")
async def get_positions(uid: str = Depends(get_current_uid)):
    from broker import get_broker
    from memory import get_key
    try:
        positions = get_broker(uid).get_positions()
        meta = get_key("positions_meta", {})
        for pos in positions:
            pos["meta"] = meta.get(pos["symbol"], {})
        return {"positions": positions, "count": len(positions)}
    except Exception as e:
        logger.error(f"Positions fetch failed: {e}")
        return {"positions": [], "count": 0, "error": str(e)}


@app.get("/api/account")
async def get_account(uid: str = Depends(get_current_uid)):
    from broker import get_broker
    try:
        return get_broker(uid).get_account()
    except Exception as e:
        logger.error(f"Account fetch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Broker unavailable: {e}")


# ── Watchlist ─────────────────────────────────────────────────────────────────

@app.get("/api/watchlist")
async def get_watchlist_endpoint(uid: str = Depends(get_current_uid)):
    from memory import get_watchlist
    return {"watchlist": get_watchlist()}


@app.post("/api/watchlist/{ticker}")
async def add_watchlist(ticker: str, uid: str = Depends(get_current_uid)):
    from memory import add_to_watchlist
    add_to_watchlist(ticker.upper())
    return {"status": "added", "ticker": ticker.upper()}


@app.delete("/api/watchlist/{ticker}")
async def remove_watchlist(ticker: str, uid: str = Depends(get_current_uid)):
    from memory import remove_from_watchlist
    remove_from_watchlist(ticker.upper())
    return {"status": "removed", "ticker": ticker.upper()}


# ── Watch Report ──────────────────────────────────────────────────────────────

@app.get("/api/watch-report")
async def get_watch_report(uid: str = Depends(get_current_uid)):
    from watch_report import get_latest_watch_report
    report = get_latest_watch_report()
    if not report:
        return {"report": None, "message": "No report generated yet"}
    return {"report": report}


# ── Leaderboard & Changelog ───────────────────────────────────────────────────

@app.get("/api/leaderboard")
async def get_leaderboard(uid: str = Depends(get_current_uid)):
    from memory import get_roster
    active = [m for m in get_roster() if m.get("status") == "active"]
    ranked = sorted(active, key=lambda m: m.get("performance_since_added", 0.0), reverse=True)
    return {"leaderboard": ranked}


@app.get("/api/changelog")
async def get_changelog_endpoint(limit: int = 50, uid: str = Depends(get_current_uid)):
    from memory import get_changelog
    log = get_changelog()
    return {"changelog": log[-limit:], "total": len(log)}
