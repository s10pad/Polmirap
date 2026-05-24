"""
MIRROR AI v2 — Streamlit Dashboard
Dark theme trading dashboard: DASHBOARD, FEED, POSITIONS, ROSTER, LEADERBOARD, WATCHLIST, LOGS.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MIRROR AI",
    page_icon="🪞",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

  /* ── Base ── */
  html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #030b14;
    color: #e2e8f0;
  }
  .stApp { background-color: #030b14; }

  /* Ambient gradient layer */
  .stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
      radial-gradient(ellipse 70% 50% at 5% 0%, rgba(0,212,170,0.07) 0%, transparent 55%),
      radial-gradient(ellipse 50% 40% at 95% 100%, rgba(56,189,248,0.05) 0%, transparent 50%),
      radial-gradient(ellipse 60% 60% at 50% 50%, rgba(167,139,250,0.02) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
  }

  .block-container {
    padding-top: 1rem !important;
    padding-bottom: 5rem !important;
    max-width: 1400px;
    position: relative;
    z-index: 1;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #04090f 0%, #060f1c 100%);
    border-right: 1px solid rgba(0,212,170,0.07);
  }
  [data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
  }

  /* ── Cards ── */
  .signal-card {
    background: rgba(6,14,26,0.85);
    border: 1px solid rgba(30,41,59,0.7);
    border-radius: 16px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow:
      0 1px 0 rgba(255,255,255,0.03) inset,
      0 4px 24px rgba(0,0,0,0.45),
      0 0 0 1px rgba(0,212,170,0.03);
    transition:
      transform 0.18s cubic-bezier(0.34,1.56,0.64,1),
      border-color 0.18s ease,
      box-shadow 0.18s ease;
  }
  .signal-card:hover {
    transform: translateY(-2px);
    border-color: rgba(0,212,170,0.18);
    box-shadow:
      0 1px 0 rgba(255,255,255,0.04) inset,
      0 8px 32px rgba(0,0,0,0.5),
      0 0 24px rgba(0,212,170,0.07);
  }

  .position-card, .roster-card {
    background: rgba(6,14,26,0.85);
    border: 1px solid rgba(30,41,59,0.7);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.35);
    transition: border-color 0.18s ease, box-shadow 0.18s ease;
  }
  .position-card:hover { border-color: rgba(56,189,248,0.18); }
  .roster-card:hover   { border-color: rgba(167,139,250,0.18); }

  .watch-card {
    background: rgba(6,14,26,0.85);
    border: 1px solid rgba(30,41,59,0.7);
    border-radius: 10px;
    padding: 0.875rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    transition: border-color 0.18s ease;
  }
  .watch-card:hover { border-color: rgba(0,212,170,0.15); }

  .stat-card {
    background: rgba(6,14,26,0.9);
    border: 1px solid rgba(30,41,59,0.7);
    border-radius: 14px;
    padding: 1.25rem 1rem;
    text-align: center;
    box-shadow:
      0 1px 0 rgba(255,255,255,0.03) inset,
      0 4px 20px rgba(0,0,0,0.4);
    transition: transform 0.18s cubic-bezier(0.34,1.56,0.64,1), border-color 0.18s ease;
  }
  .stat-card:hover {
    transform: translateY(-2px);
    border-color: rgba(0,212,170,0.12);
  }

  /* ── Metrics ── */
  .metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.1;
  }
  .metric-label {
    font-size: 0.7rem;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin-top: 0.3rem;
  }

  /* ── Colors ── */
  .green  { color: #00d4aa; }
  .red    { color: #ff4757; }
  .blue   { color: #38bdf8; }
  .amber  { color: #ffa502; }
  .purple { color: #a78bfa; }
  .muted  { color: #475569; }

  /* ── Badges ── */
  .badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 6px;
    font-size: 0.69rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.04em;
  }
  .badge-green  { background: rgba(0,212,170,0.12);  color: #00d4aa; border: 1px solid rgba(0,212,170,0.22); }
  .badge-red    { background: rgba(255,71,87,0.12);   color: #ff4757; border: 1px solid rgba(255,71,87,0.22); }
  .badge-blue   { background: rgba(56,189,248,0.12);  color: #38bdf8; border: 1px solid rgba(56,189,248,0.22); }
  .badge-amber  { background: rgba(255,165,2,0.12);   color: #ffa502; border: 1px solid rgba(255,165,2,0.22); }
  .badge-purple { background: rgba(167,139,250,0.12); color: #a78bfa; border: 1px solid rgba(167,139,250,0.22); }

  /* ── Empty states ── */
  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
  }
  .empty-state .icon  { font-size: 2.25rem; margin-bottom: 0.75rem; opacity: 0.5; }
  .empty-state .title { font-size: 0.95rem; font-weight: 600; color: #475569; margin-bottom: 0.4rem; }
  .empty-state .hint  { font-size: 0.8rem; color: #2d3f55; max-width: 260px; margin: 0 auto; line-height: 1.6; }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0.2rem;
    background: rgba(6,14,26,0.9);
    border-radius: 12px;
    padding: 0.3rem;
    border: 1px solid rgba(30,41,59,0.6);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
  .stTabs [data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.8rem;
    color: #475569;
    border-radius: 8px;
    padding: 0.5rem 0.8rem;
    white-space: nowrap;
    min-height: 36px;
    transition: color 0.15s ease, background 0.15s ease;
  }
  .stTabs [aria-selected="true"] {
    color: #00d4aa !important;
    background: rgba(0,212,170,0.09) !important;
  }
  .stTabs [data-baseweb="tab-highlight"] { display: none; }
  .stTabs [data-baseweb="tab-border"]    { display: none; }

  /* ── Buttons ── */
  .stButton > button {
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    min-height: 42px;
    border: 1px solid rgba(30,41,59,0.9) !important;
    background: rgba(6,14,26,0.95) !important;
    color: #94a3b8 !important;
    transition:
      transform 0.15s cubic-bezier(0.34,1.56,0.64,1),
      border-color 0.15s ease,
      color 0.15s ease,
      box-shadow 0.15s ease !important;
  }
  .stButton > button:hover {
    border-color: rgba(0,212,170,0.35) !important;
    color: #00d4aa !important;
    box-shadow: 0 0 18px rgba(0,212,170,0.1) !important;
    transform: translateY(-1px);
  }
  .stButton > button:active { transform: scale(0.98) !important; }
  .stButton > button[kind="primary"] {
    background: rgba(0,212,170,0.12) !important;
    border-color: rgba(0,212,170,0.35) !important;
    color: #00d4aa !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: rgba(0,212,170,0.22) !important;
    box-shadow: 0 0 24px rgba(0,212,170,0.15) !important;
  }

  /* ── Inputs ── */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea {
    background: rgba(6,14,26,0.95) !important;
    border: 1px solid rgba(30,41,59,0.8) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.9rem !important;
  }
  .stTextInput > div > div > input:focus,
  .stTextArea > div > div > textarea:focus {
    border-color: rgba(0,212,170,0.4) !important;
    box-shadow: 0 0 0 3px rgba(0,212,170,0.06) !important;
  }
  .stSelectbox > div > div {
    background: rgba(6,14,26,0.95) !important;
    border: 1px solid rgba(30,41,59,0.8) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
  }

  /* ── Metrics native ── */
  [data-testid="stMetric"] {
    background: rgba(6,14,26,0.8);
    border: 1px solid rgba(30,41,59,0.6);
    border-radius: 12px;
    padding: 1rem;
  }
  [data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 1.4rem !important;
    letter-spacing: -0.02em;
  }

  /* ── Alerts ── */
  [data-testid="stAlert"] {
    border-radius: 10px;
    border: 1px solid rgba(255,165,2,0.25) !important;
    background: rgba(255,165,2,0.06) !important;
  }

  /* ── Expanders ── */
  [data-testid="stExpander"] {
    border: 1px solid rgba(30,41,59,0.6) !important;
    border-radius: 10px !important;
    background: rgba(6,14,26,0.7) !important;
  }

  /* ── Dividers ── */
  hr {
    border-color: rgba(30,41,59,0.45) !important;
    margin: 1rem 0 !important;
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(30,41,59,0.9); border-radius: 4px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(0,212,170,0.35); }

  /* ── Mobile ── */
  @media (max-width: 768px) {
    .block-container {
      padding: 0.5rem 0.75rem !important;
      padding-bottom: 5.5rem !important;
    }
    .metric-value { font-size: 1.1rem; }
    .signal-card  { padding: 1rem; border-radius: 12px; }
    .stat-card    { padding: 0.875rem 0.5rem; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] {
      padding: 0.4rem 0.6rem;
      font-size: 0.73rem;
    }
    .stButton > button { min-height: 48px; font-size: 0.875rem !important; }
    /* Collapse 4-col grids to 2-col on tablets */
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
      min-width: 45% !important;
    }
  }
  @media (max-width: 480px) {
    .metric-value { font-size: 1rem; }
    /* Full-width single column on small phones */
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
      min-width: 100% !important;
    }
    .stat-card { margin-bottom: 0.5rem; }
  }
</style>
""", unsafe_allow_html=True)


# ── Data helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_alpaca_account():
    """Fetch Alpaca account equity, buying power, today P&L, and open positions. Cached 30s."""
    try:
        from alpaca.trading.client import TradingClient
        client = TradingClient(
            os.getenv("ALPACA_KEY", ""),
            os.getenv("ALPACA_SECRET", ""),
            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true",
        )
        account = client.get_account()
        positions = client.get_all_positions()
        return {
            "equity": float(account.equity),
            "buying_power": float(account.buying_power),
            "today_pl": float(account.equity) - float(account.last_equity),
            "positions": positions,
        }
    except Exception as e:
        return {"equity": 0, "buying_power": 0, "today_pl": 0, "positions": [], "error": str(e)}


@st.cache_data(ttl=300)
def get_portfolio_history_data() -> dict:
    """Fetch 30-day portfolio equity curve from Alpaca. Cached 5min."""
    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import GetPortfolioHistoryRequest
        client = TradingClient(
            os.getenv("ALPACA_KEY", ""),
            os.getenv("ALPACA_SECRET", ""),
            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true",
        )
        history = client.get_portfolio_history(
            GetPortfolioHistoryRequest(period="1M", timeframe="1D")
        )
        timestamps = [
            datetime.fromtimestamp(t).strftime("%m/%d")
            for t in (history.timestamp or [])
        ]
        equity = [float(e) if e else None for e in (history.equity or [])]
        return {"dates": timestamps, "equity": equity}
    except Exception as e:
        return {"dates": [], "equity": [], "error": str(e)}


@st.cache_data(ttl=300)
def get_sparkline_data(ticker: str) -> list:
    """Return up to 7 recent closing prices for a ticker sparkline. Cached 5min."""
    from fetcher import get_alpaca_bars
    bars = get_alpaca_bars(ticker, days=10)
    return [b["close"] for b in bars[-7:]] if bars else []


@st.cache_data(ttl=60)
def get_ticker_quote(ticker: str) -> dict:
    """Return current price and today's % change for a ticker. Cached 1min."""
    from fetcher import get_alpaca_bars
    bars = get_alpaca_bars(ticker, days=3)
    if len(bars) >= 2:
        prev = bars[-2]["close"]
        curr = bars[-1]["close"]
        return {"price": curr, "change_pct": round(((curr - prev) / prev) * 100, 2)}
    if len(bars) == 1:
        return {"price": bars[0]["close"], "change_pct": None}
    return {"price": None, "change_pct": None}


@st.cache_data(ttl=600)
def get_alpaca_news(ticker: str) -> list:
    """Fetch up to 4 recent news headlines for a ticker from Alpaca News API. Cached 10min."""
    try:
        from alpaca.data import NewsClient
        from alpaca.data.requests import NewsRequest
        client = NewsClient(
            api_key=os.getenv("ALPACA_KEY", ""),
            secret_key=os.getenv("ALPACA_SECRET", ""),
        )
        resp = client.get_news(NewsRequest(symbols=[ticker], limit=4))
        results = []
        for item in (resp.news if hasattr(resp, "news") else []):
            try:
                updated = getattr(item, "updated_at", None) or getattr(item, "created_at", None)
                if updated:
                    age = datetime.now() - updated.replace(tzinfo=None)
                    hours = int(age.total_seconds() / 3600)
                    age_str = f"{hours}h ago" if hours < 24 else f"{age.days}d ago"
                else:
                    age_str = ""
                results.append({
                    "headline": getattr(item, "headline", ""),
                    "source": getattr(item, "source", ""),
                    "age": age_str,
                    "url": getattr(item, "url", ""),
                })
            except Exception:
                continue
        return results
    except Exception:
        return []


def make_sparkline_svg(closes: list, width: int = 80, height: int = 28) -> str:
    """Render a compact inline SVG polyline from a list of closing prices."""
    if not closes or len(closes) < 2:
        return ""
    mn, mx = min(closes), max(closes)
    rng = mx - mn or 1
    pts = []
    for i, c in enumerate(closes):
        x = round(i / (len(closes) - 1) * width, 1)
        y = round(height - ((c - mn) / rng * (height - 2)) - 1, 1)
        pts.append(f"{x},{y}")
    color = "#00d4aa" if closes[-1] >= closes[0] else "#ff4757"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="display:inline-block;vertical-align:middle">'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" '
        f'stroke-width="1.5" stroke-linejoin="round"/></svg>'
    )


def risk_blocks(score: float) -> str:
    """5-block visual conviction indicator. More filled blocks = stronger signal."""
    filled = min(5, max(1, round(score / 2)))
    color = "#00d4aa" if filled <= 2 else "#ffa502" if filled == 3 else "#ff4757"
    return (
        f'<span style="color:{color};font-family:Space Mono,monospace;letter-spacing:2px">'
        f'{"█" * filled}{"░" * (5 - filled)}</span>'
    )


def fmt_money(val: float) -> str:
    """Format a dollar value with commas and 2 decimal places."""
    return f"${val:,.2f}"


def fmt_pct(val: float) -> str:
    """Format a percentage with explicit sign."""
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.2f}%"


def color_pct(val: float) -> str:
    """Return CSS class name based on positive/negative value."""
    return "green" if val >= 0 else "red"


def empty_state(icon: str, title: str, hint: str) -> None:
    """Centered empty state with icon, short title, and plain-English next step."""
    st.markdown(
        f'<div class="empty-state">'
        f'<div class="icon">{icon}</div>'
        f'<div class="title">{title}</div>'
        f'<div class="hint">{hint}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    """Live portfolio metrics and autonomy mode controls."""
    from memory import get_autonomy_mode, set_autonomy_mode, append_changelog

    with st.sidebar:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1rem">
          <span style="font-size:1.3rem">🪞</span>
          <span style="font-weight:700;font-size:1rem;letter-spacing:-0.02em">MIRROR AI</span>
          <span style="font-family:'Space Mono',monospace;font-size:0.6rem;color:#475569;
                       border:1px solid #1e293b;border-radius:4px;padding:0.1rem 0.3rem">v2</span>
        </div>
        """, unsafe_allow_html=True)

        acct = get_alpaca_account()
        equity = acct.get("equity", 0)
        today_pl = acct.get("today_pl", 0)
        buying_power = acct.get("buying_power", 0)
        pl_class = color_pct(today_pl)
        pl_sign = "+" if today_pl >= 0 else ""

        # Portfolio metric block
        st.markdown(f"""
        <div style="background:rgba(0,212,170,0.04);border:1px solid rgba(0,212,170,0.1);
                    border-radius:12px;padding:1rem;margin-bottom:0.75rem">
          <div class="metric-label">Portfolio Value</div>
          <div class="metric-value" style="font-size:1.5rem">{fmt_money(equity)}</div>
          <div style="margin-top:0.5rem;display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:0.75rem;color:#475569">Today P&amp;L</span>
            <span class="{pl_class}" style="font-family:'Space Mono',monospace;
                          font-size:0.85rem;font-weight:700">{pl_sign}{fmt_money(today_pl)}</span>
          </div>
          <div style="margin-top:0.4rem;display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:0.75rem;color:#475569">Buying Power</span>
            <span style="font-family:'Space Mono',monospace;font-size:0.8rem;
                         color:#94a3b8">{fmt_money(buying_power)}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        mode = get_autonomy_mode()
        mode_color = "#ffa502" if mode == "full" else "#38bdf8"
        mode_bg = "rgba(255,165,2,0.08)" if mode == "full" else "rgba(56,189,248,0.08)"
        mode_label = "⚡ FULL AUTO" if mode == "full" else "🔒 CONTROLLED"
        st.markdown(f"""
        <div style="background:{mode_bg};border:1px solid {mode_color}22;border-radius:8px;
                    padding:0.6rem 0.8rem;margin-bottom:0.75rem;
                    display:flex;align-items:center;justify-content:space-between">
          <span style="font-size:0.72rem;color:#475569;text-transform:uppercase;letter-spacing:0.06em">Mode</span>
          <span style="color:{mode_color};font-weight:700;font-size:0.85rem">{mode_label}</span>
        </div>
        """, unsafe_allow_html=True)

        if mode == "controlled":
            if st.button("Switch to FULL autonomy", width='stretch'):
                st.session_state["confirm_full_mode"] = True

        if st.session_state.get("confirm_full_mode"):
            st.warning(
                "⚠️ FULL mode executes trades immediately on high-confidence signals. No veto window."
            )
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Confirm", type="primary"):
                    set_autonomy_mode("full")
                    append_changelog(
                        f"[{datetime.now().strftime('%Y-%m-%d')}] MODE CHANGE — Switched to FULL via dashboard."
                    )
                    st.session_state["confirm_full_mode"] = False
                    st.rerun()
            with col_b:
                if st.button("Cancel"):
                    st.session_state["confirm_full_mode"] = False
                    st.rerun()
        elif mode == "full":
            if st.button("Switch to CONTROLLED", width='stretch'):
                set_autonomy_mode("controlled")
                append_changelog(
                    f"[{datetime.now().strftime('%Y-%m-%d')}] MODE CHANGE — Switched to CONTROLLED via dashboard."
                )
                st.rerun()

        st.markdown("---")
        st.markdown(
            f'<div style="font-size:0.68rem;color:#2d3f55;text-align:center;margin-bottom:0.5rem">'
            f'Last sync: <span style="color:#334155;font-family:Space Mono,monospace">'
            f'{datetime.now().strftime("%H:%M:%S")}</span></div>',
            unsafe_allow_html=True,
        )
        if st.button("🔄 Refresh Data", width='stretch'):
            st.cache_data.clear()
            st.rerun()

        if acct.get("error"):
            st.error(f"Alpaca: {acct['error'][:80]}")


# ── Tab: DASHBOARD ────────────────────────────────────────────────────────────

def render_dashboard():
    """Landing overview: pending signal counts by category, equity curve vs SPY, allocation, top movers."""
    import plotly.graph_objects as go
    from memory import get_pending_signals, get_roster, get_open_positions_meta

    st.markdown('<div style="font-size:1.1rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;color:#e2e8f0">📊 Overview</div>', unsafe_allow_html=True)

    signals = get_pending_signals()
    pending = [s for s in signals if s.get("status") == "pending"]
    roster = get_roster()
    member_cats = {m["name"]: m.get("category", "public_figure") for m in roster}

    # ── Signal count cards per category ──
    cat_counts: dict = {"politician": 0, "ceo": 0, "athlete": 0, "public_figure": 0}
    for s in pending:
        for buyer in s.get("buyers", []):
            cat = member_cats.get(buyer.get("name", ""), "public_figure")
            if cat in cat_counts:
                cat_counts[cat] += 1

    cat_meta = {
        "politician":    ("🏛️", "Politicians",    "#38bdf8"),
        "ceo":           ("💼", "CEOs",            "#a78bfa"),
        "athlete":       ("🏆", "Athletes",        "#ffa502"),
        "public_figure": ("⭐", "Public Figures",  "#00d4aa"),
    }
    cols = st.columns(4)
    for i, (cat, (icon, label, color)) in enumerate(cat_meta.items()):
        count = cat_counts.get(cat, 0)
        with cols[i]:
            st.markdown(
                f'<div class="stat-card">'
                f'<div style="font-size:1.4rem">{icon}</div>'
                f'<div class="metric-value" style="color:{color}">{count}</div>'
                f'<div class="metric-label">{label} signals</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Equity curve + SPY baseline | Allocation chart ──
    col_chart, col_alloc = st.columns([3, 2])

    with col_chart:
        st.markdown("#### Equity vs SPY (30 days)")
        hist = get_portfolio_history_data()
        dates = hist.get("dates", [])
        equity_vals = hist.get("equity", [])

        if dates and any(v for v in equity_vals if v):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=equity_vals,
                mode="lines", name="Portfolio",
                line=dict(color="#00d4aa", width=2),
                fill="tozeroy", fillcolor="rgba(0,212,170,0.06)",
            ))
            try:
                spy_closes = get_sparkline_data("SPY")
                base_equity = next((v for v in equity_vals if v), None)
                if spy_closes and base_equity and spy_closes[0]:
                    spy_norm = [base_equity * (p / spy_closes[0]) for p in spy_closes]
                    spy_dates = dates[-len(spy_norm):]
                    fig.add_trace(go.Scatter(
                        x=spy_dates, y=spy_norm,
                        mode="lines", name="SPY (normalized)",
                        line=dict(color="#475569", width=1.5, dash="dot"),
                    ))
            except Exception:
                pass

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Space Grotesk"),
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", y=1.05, x=0, font=dict(size=11)),
                xaxis=dict(showgrid=False, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor="#0a0f1a", tickformat="$,.0f", tickfont=dict(size=10)),
                height=210,
            )
            st.plotly_chart(fig, width='stretch')
        else:
            empty_state(
                "📈", "No equity history yet",
                "Populates after the first trading day with at least one executed position."
            )

    with col_alloc:
        st.markdown("#### Allocation by Category")
        acct = get_alpaca_account()
        positions = acct.get("positions", [])
        meta = get_open_positions_meta()

        if positions:
            alloc: dict = {}
            cat_colors = {
                "politician": "#38bdf8", "ceo": "#a78bfa",
                "athlete": "#ffa502", "public_figure": "#00d4aa", "unknown": "#334155",
            }
            for p in positions:
                sym = p.symbol
                triggerers = meta.get(sym, {}).get("triggered_by", [])
                cat = "unknown"
                for name in triggerers:
                    cat = member_cats.get(name, "unknown")
                    break
                alloc[cat] = alloc.get(cat, 0.0) + float(p.market_value or 0)

            fig2 = go.Figure(go.Bar(
                x=list(alloc.keys()),
                y=list(alloc.values()),
                marker_color=[cat_colors.get(k, "#334155") for k in alloc],
                text=[fmt_money(v) for v in alloc.values()],
                textposition="outside",
                textfont=dict(size=10, color="#94a3b8"),
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Space Grotesk"),
                margin=dict(l=0, r=0, t=10, b=30),
                xaxis=dict(showgrid=False, tickfont=dict(size=10)),
                yaxis=dict(showgrid=False, visible=False),
                showlegend=False, height=210,
            )
            st.plotly_chart(fig2, width='stretch')
        else:
            empty_state(
                "🧩", "No positions yet",
                "Category allocations appear here once you've mirrored at least one trade."
            )

    # ── Top mover tiles ──
    st.markdown("#### Top Movers")
    acct2 = get_alpaca_account()
    positions2 = acct2.get("positions", [])
    if positions2:
        top4 = sorted(positions2, key=lambda p: abs(float(p.unrealized_plpc or 0)), reverse=True)[:4]
        tile_cols = st.columns(len(top4))
        for i, pos in enumerate(top4):
            sym = pos.symbol
            pct = float(pos.unrealized_plpc or 0) * 100
            pl = float(pos.unrealized_pl or 0)
            cls = "green" if pct >= 0 else "red"
            with tile_cols[i]:
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div style="font-weight:700;font-size:1rem">${sym}</div>'
                    f'<div class="metric-value {cls}">{fmt_pct(pct)}</div>'
                    f'<div class="muted" style="font-size:0.78rem">{fmt_money(pl)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        empty_state(
            "📉", "No open positions",
            "Top movers will rank here once trades are executed."
        )


# ── Tab: FEED ─────────────────────────────────────────────────────────────────

def render_feed():
    """Signal feed with filter bar, enhanced cards (live price + sparkline + risk blocks + news)."""
    from memory import (
        get_pending_signals, set_pending_signals,
        add_vetoed_ticker, append_changelog,
        get_watchlist, add_to_watchlist,
    )

    st.markdown('<div style="font-size:1.1rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;color:#e2e8f0">📡 Signal Feed</div>', unsafe_allow_html=True)

    all_signals = get_pending_signals()
    if not all_signals:
        empty_state(
            "📡", "No signals yet",
            "The system runs every weekday at 7:30am ET and bootstraps your roster on first run."
        )
        return

    # ── Filter bar ──
    col_action, col_sort, col_show, col_search = st.columns([1, 1, 1, 2])
    with col_action:
        action_filter = st.selectbox(
            "Action", ["All", "BUY", "SELL"],
            key="ff_action", label_visibility="collapsed",
        )
    with col_sort:
        sort_by = st.selectbox(
            "Sort", ["Score ↓", "Conviction ↓", "Newest"],
            key="ff_sort", label_visibility="collapsed",
        )
    with col_show:
        show_filter = st.selectbox(
            "Show", ["Pending only", "All", "Reviewed"],
            key="ff_show", label_visibility="collapsed",
        )
    with col_search:
        search = st.text_input(
            "Search", placeholder="Ticker or investor name",
            key="ff_search", label_visibility="collapsed",
        )

    filtered = list(all_signals)
    if action_filter != "All":
        filtered = [s for s in filtered if s.get("action", "BUY") == action_filter]
    if show_filter == "Pending only":
        filtered = [s for s in filtered if s.get("status") == "pending"]
    elif show_filter == "Reviewed":
        filtered = [s for s in filtered if s.get("status") != "pending"]
    if search:
        q = search.upper()
        filtered = [
            s for s in filtered
            if q in s.get("ticker", "").upper()
            or any(q in b.get("name", "").upper() for b in s.get("buyers", []))
        ]
    if sort_by == "Score ↓":
        filtered.sort(key=lambda s: s.get("score", 0), reverse=True)
    elif sort_by == "Conviction ↓":
        filtered.sort(key=lambda s: s.get("conviction", 0), reverse=True)

    if not filtered:
        empty_state("🔍", "No signals match your filters", "Adjust the filter bar above to see more.")
        return

    pending = [s for s in filtered if s.get("status") == "pending"]
    reviewed = [s for s in filtered if s.get("status") != "pending"]
    watchlist = get_watchlist()

    # ── Pending signal cards ──
    for signal in pending:
        ticker = signal["ticker"]
        quote = get_ticker_quote(ticker)
        closes = get_sparkline_data(ticker)
        sparkline = make_sparkline_svg(closes)
        news = get_alpaca_news(ticker)

        price_str = fmt_money(quote["price"]) if quote.get("price") else "—"
        chg = quote.get("change_pct")
        if chg is not None:
            badge_cls = "badge-green" if chg >= 0 else "badge-red"
            chg_html = f'<span class="badge {badge_cls}">{fmt_pct(chg)}</span>'
        else:
            chg_html = ""

        buyers_html = " &middot; ".join(
            f'<span class="muted" style="font-size:0.8rem">{b["name"]} ({b.get("portfolio_pct",0):.1f}%)</span>'
            for b in signal.get("buyers", [])
        )

        action_color = "#00d4aa" if signal.get("action", "BUY") == "BUY" else "#ff4757"
        with st.container():
            st.markdown(f"""
            <div class="signal-card" style="border-left:3px solid {action_color}40">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem">
                <div style="display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap">
                  <span style="font-size:1.4rem;font-weight:700;color:#00d4aa;
                               font-family:'Space Mono',monospace">${ticker}</span>
                  <span class="badge" style="background:rgba(0,212,170,0.08);color:{action_color};
                                             border:1px solid {action_color}33;font-size:0.65rem">
                    {signal.get('action','BUY')}
                  </span>
                  <span style="font-family:'Space Mono',monospace;font-size:0.95rem;
                               color:#94a3b8">{price_str}</span>
                  {chg_html}
                </div>
                <div style="display:flex;align-items:center;gap:0.75rem">
                  {sparkline}
                  <span style="font-family:'Space Mono',monospace;color:#38bdf8;
                               font-size:0.82rem;font-weight:700">
                    {signal['score']:.2f}
                  </span>
                </div>
              </div>
              <div style="margin:0.6rem 0 0.4rem;display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center">
                <span class="badge badge-blue">{signal['conviction']}</span>
                <span style="font-size:0.78rem;color:#475569">{signal.get('sector','—')}</span>
                <span style="font-size:0.78rem;color:#475569">Risk:</span>
                {risk_blocks(signal['score'])}
              </div>
              <div style="margin:0.4rem 0;font-size:0.84rem;color:#94a3b8;line-height:1.55">{signal['reasoning']}</div>
              <div style="margin-top:0.5rem;display:flex;flex-wrap:wrap;gap:0.3rem">{buyers_html}</div>
              <div style="margin-top:0.5rem;color:#334155;font-size:0.75rem;
                           font-family:'Space Mono',monospace">
                Size: {signal['position_pct']:.1f}% · {fmt_money(signal['position_usd'])}
              </div>
            </div>
            """, unsafe_allow_html=True)

            btn_cols = st.columns([1, 1, 1.2, 3.5])
            with btn_cols[0]:
                if st.button("✅ Approve", key=f"approve_{signal['signal_id']}"):
                    for s in all_signals:
                        if s["signal_id"] == signal["signal_id"]:
                            s["status"] = "approved"
                    set_pending_signals(all_signals)
                    append_changelog(
                        f"[{datetime.now().strftime('%Y-%m-%d')}] APPROVED {ticker} — Approved via dashboard."
                    )
                    st.rerun()
            with btn_cols[1]:
                if st.button("⏭️ Skip", key=f"skip_{signal['signal_id']}"):
                    add_vetoed_ticker(ticker)
                    for s in all_signals:
                        if s["signal_id"] == signal["signal_id"]:
                            s["status"] = "skipped"
                    set_pending_signals(all_signals)
                    append_changelog(
                        f"[{datetime.now().strftime('%Y-%m-%d')}] SKIPPED {ticker} — Skipped via dashboard."
                    )
                    st.rerun()
            with btn_cols[2]:
                wl_label = "✓ Watching" if ticker in watchlist else "+ Watchlist"
                if st.button(wl_label, key=f"wl_{signal['signal_id']}"):
                    add_to_watchlist(ticker)
                    st.rerun()

            # News + deep-dive expander
            with st.expander(f"📰 News — ${ticker}"):
                if news:
                    for item in news:
                        st.markdown(
                            f'<div style="padding:0.4rem 0;border-bottom:1px solid #0a0f1a">'
                            f'<span style="font-size:0.85rem">{item["headline"]}</span>'
                            f'<span class="muted" style="font-size:0.75rem;margin-left:0.6rem">'
                            f'{item["source"]} · {item["age"]}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown('<span class="muted" style="font-size:0.85rem">No recent headlines found.</span>', unsafe_allow_html=True)

    # ── Reviewed signal rows ──
    if reviewed:
        st.markdown("#### Reviewed")
        for s in reviewed[-30:]:
            status_color = "#00d4aa" if s["status"] == "approved" else "#334155"
            st.markdown(
                f'<div style="color:{status_color};padding:0.25rem 0;border-bottom:1px solid #0a0f1a;'
                f'font-size:0.8rem;font-family:Space Mono,monospace">'
                f'${s["ticker"]} — {s["status"].upper()} | Score: {s["score"]:.2f} | Conviction: {s["conviction"]}'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Tab: POSITIONS ────────────────────────────────────────────────────────────

def render_positions():
    """Open Alpaca positions with P&L, stop-loss distance, and exit with confirmation."""
    from memory import get_open_positions_meta, append_changelog

    st.markdown('<div style="font-size:1.1rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;color:#e2e8f0">💼 Open Positions</div>', unsafe_allow_html=True)
    acct = get_alpaca_account()
    positions = acct.get("positions", [])
    meta = get_open_positions_meta()

    total_equity = acct.get("equity", 0)
    total_unrealized = sum(float(p.unrealized_pl or 0) for p in positions)
    col1, col2 = st.columns(2)
    col1.metric("Portfolio Value", fmt_money(total_equity))
    col2.metric(
        "Unrealized P&L", fmt_money(total_unrealized),
        delta=f"{(total_unrealized / total_equity * 100):.2f}%" if total_equity > 0 else None,
    )

    if not positions:
        st.markdown("---")
        empty_state(
            "💼", "No open positions",
            "Mirrored signals appear in the Feed tab. After approval (or the veto window), positions show here."
        )
        return

    st.markdown("---")
    stop_loss_pct = float(os.getenv("STOP_LOSS_PCT", "15"))

    for pos in positions:
        sym = pos.symbol
        entry = float(meta.get(sym, {}).get("entry_price", pos.avg_entry_price or 0))
        current = float(pos.current_price or 0)
        unrealized = float(pos.unrealized_pl or 0)
        unrealized_pct = float(pos.unrealized_plpc or 0) * 100
        market_val = float(pos.market_value or 0)
        triggered_by = meta.get(sym, {}).get("triggered_by", [])
        entry_date = meta.get(sym, {}).get("entry_date", "unknown")

        days_held = 0
        try:
            days_held = (datetime.now() - datetime.strptime(entry_date, "%Y-%m-%d")).days
        except Exception:
            pass

        sl_distance = (
            ((current - entry * (1 - stop_loss_pct / 100)) / current * 100)
            if current > 0 else 0
        )
        pl_class = color_pct(unrealized_pct)

        st.markdown(f"""
        <div class="position-card">
          <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.25rem">
            <span style="font-weight:700;font-size:1.1rem">${sym}</span>
            <span class="{pl_class}" style="font-family:'Space Mono',monospace">
              {fmt_pct(unrealized_pct)} ({fmt_money(unrealized)})
            </span>
          </div>
          <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.25rem">
            Entry: {fmt_money(entry)} → Current: {fmt_money(current)} |
            Value: {fmt_money(market_val)} | {days_held}d held
          </div>
          <div style="color:#64748b;font-size:0.78rem;margin-top:0.2rem">
            Triggered by: {', '.join(triggered_by) or 'unknown'} |
            Stop-loss distance: {sl_distance:.1f}%
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Exit ${sym}", key=f"exit_{sym}"):
            st.session_state[f"confirm_exit_{sym}"] = True

        if st.session_state.get(f"confirm_exit_{sym}"):
            st.warning(f"Confirm exit of ${sym}? This will place a market sell order immediately.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirm Exit", key=f"confirm_{sym}", type="primary"):
                    try:
                        from alpaca.trading.client import TradingClient
                        client = TradingClient(
                            os.getenv("ALPACA_KEY", ""),
                            os.getenv("ALPACA_SECRET", ""),
                            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true",
                        )
                        client.close_position(sym)
                        append_changelog(
                            f"[{datetime.now().strftime('%Y-%m-%d')}] EXIT {sym} — Position closed via dashboard."
                        )
                        st.cache_data.clear()
                        st.session_state[f"confirm_exit_{sym}"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Exit failed: {e}")
            with c2:
                if st.button("Cancel", key=f"cancel_exit_{sym}"):
                    st.session_state[f"confirm_exit_{sym}"] = False
                    st.rerun()


# ── Tab: ROSTER ───────────────────────────────────────────────────────────────

def render_roster():
    """Roster members, pending review proposals, and manual add/remove overrides."""
    from memory import get_roster, get_review_proposal
    from roster import apply_review_proposal, add_member, remove_member

    st.markdown('<div style="font-size:1.1rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;color:#e2e8f0">👥 Roster</div>', unsafe_allow_html=True)
    roster = get_roster()
    proposal = get_review_proposal()

    if proposal:
        st.markdown("#### ⚠️ Pending Review Proposal")
        st.markdown(f"**Summary:** {proposal.get('summary', '')}")
        for c in proposal.get("changes", []):
            icon = {"remove": "🔴", "add": "🟢", "weight_update": "🔵", "keep": "⚪"}.get(c["action"], "•")
            st.markdown(f"{icon} **{c['action'].upper()}** {c['name']}: {c['reason']}")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ APPROVE ALL CHANGES", type="primary", width='stretch'):
                n, actions = apply_review_proposal(proposal)
                st.success(f"Applied {n} changes.")
                st.rerun()
        with col_b:
            if st.button("❌ Reject All", width='stretch'):
                from memory import clear_review_proposal
                clear_review_proposal()
                st.rerun()
        st.markdown("---")

    if not roster:
        empty_state(
            "👥", "Roster not yet initialized",
            "Auto-bootstraps at 7:30am ET on first run via Brave Search + AI. No names are hardcoded."
        )
    else:
        st.markdown(f"#### Active Members ({len(roster)})")
        for i, m in enumerate(sorted(roster, key=lambda x: x.get("weight", 0), reverse=True), 1):
            weight = m.get("weight", 1.0)
            perf = m.get("performance_since_added", 0.0)
            perf_class = color_pct(perf)

            st.markdown(f"""
            <div class="roster-card">
              <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap">
                <span style="font-weight:700">{i}. {m['name']}</span>
                <span class="{perf_class}" style="font-family:'Space Mono',monospace">{fmt_pct(perf)}</span>
              </div>
              <div style="color:#94a3b8;font-size:0.85rem">{m.get('category','').upper()} | Weight: {weight:.2f}</div>
              <div style="color:#64748b;font-size:0.8rem;margin-top:0.25rem">{m.get('why_added','')}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Remove {m['name']}", key=f"remove_{i}"):
                remove_member(m["name"], "Manually removed by owner via dashboard.")
                st.rerun()

    st.markdown("---")
    st.markdown("#### Manual Override — Add Member")
    with st.expander("Add a new person to the roster"):
        new_name = st.text_input("Name")
        new_cat = st.selectbox("Category", ["politician", "ceo", "athlete", "public_figure"])
        new_reason = st.text_area("Why add them?")
        new_weight = st.slider("Starting weight", 0.5, 1.6, 1.0, 0.05)
        if st.button("Add to Roster") and new_name and new_reason:
            add_member({
                "name": new_name, "category": new_cat,
                "why_added": new_reason, "weight": new_weight,
            })
            st.rerun()


# ── Tab: LEADERBOARD ──────────────────────────────────────────────────────────

def render_leaderboard():
    """Ranked roster members with clickable profile drilldown showing bio + current signals."""
    from memory import get_roster, get_pending_signals

    # ── Profile drilldown ──
    selected = st.session_state.get("leaderboard_selected")
    if selected:
        roster = get_roster()
        member = next((m for m in roster if m["name"] == selected), None)
        if not member:
            st.session_state["leaderboard_selected"] = None
            st.rerun()
            return

        signals = get_pending_signals()
        member_signals = [
            s for s in signals
            if any(b.get("name") == selected for b in s.get("buyers", []))
        ]

        if st.button("← Back to Leaderboard"):
            st.session_state["leaderboard_selected"] = None
            st.rerun()

        perf = member.get("performance_since_added", 0.0)
        weight = member.get("weight", 1.0)
        perf_badge = "badge-green" if perf >= 0 else "badge-red"

        st.markdown(f"### {member['name']}")
        st.markdown(
            f'<span class="badge badge-blue">{member.get("category","").upper()}</span>'
            f'&nbsp;<span class="badge badge-amber">Weight {weight:.2f}</span>'
            f'&nbsp;<span class="badge {perf_badge}">{fmt_pct(perf)}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"**Why added:** {member.get('why_added', '—')}")
        st.markdown(
            f"**Added:** {member.get('added_date', '—')} | "
            f"**Last reviewed:** {member.get('last_reviewed', '—')}"
        )

        st.markdown("---")
        st.markdown(f"#### Active in {len(member_signals)} current signal(s)")
        if member_signals:
            for s in member_signals:
                pct = next(
                    (b.get("portfolio_pct", 0) for b in s["buyers"] if b["name"] == selected), 0
                )
                st.markdown(
                    f'<div style="padding:0.4rem 0;border-bottom:1px solid #0a0f1a;font-size:0.85rem">'
                    f'<b style="color:#00d4aa">${s["ticker"]}</b>'
                    f' — Score {s["score"]:.2f} | {pct:.1f}% of their portfolio | {s.get("sector","—")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<span class="muted">Not appearing in any current pending signals.</span>', unsafe_allow_html=True)
        return

    # ── Ranked list ──
    st.markdown('<div style="font-size:1.1rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;color:#e2e8f0">🏆 Leaderboard</div>', unsafe_allow_html=True)
    roster = get_roster()

    if not roster:
        empty_state(
            "🏆", "Roster not yet initialized",
            "The leaderboard ranks members after the first roster bootstrap."
        )
        return

    ranked = sorted(roster, key=lambda m: m.get("performance_since_added", 0.0), reverse=True)
    medals = ["🥇", "🥈", "🥉"]

    for i, m in enumerate(ranked):
        medal = medals[i] if i < 3 else f"{i+1}."
        perf = m.get("performance_since_added", 0.0)
        weight = m.get("weight", 1.0)
        perf_class = color_pct(perf)
        trend = "↑" if perf > 0 else "↓" if perf < 0 else "→"

        col_info, col_btn = st.columns([6, 1])
        perf_glow = "rgba(0,212,170,0.06)" if perf >= 0 else "rgba(255,71,87,0.06)"
        with col_info:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;
                        padding:0.875rem 1rem;background:rgba(6,14,26,0.9);border-radius:12px;
                        margin-bottom:0.5rem;border:1px solid rgba(30,41,59,0.7);
                        box-shadow:0 2px 12px rgba(0,0,0,0.3),0 0 0 1px {perf_glow}">
              <div style="display:flex;align-items:center;gap:0.5rem">
                <span style="font-size:1.1rem">{medal}</span>
                <span style="font-weight:700;font-size:0.95rem">{m['name']}</span>
              </div>
              <span class="badge badge-blue" style="font-size:0.62rem">{m.get('category','').upper()}</span>
              <span style="font-family:'Space Mono',monospace;color:#475569;font-size:0.78rem">W {weight:.2f}</span>
              <span class="{perf_class}" style="font-family:'Space Mono',monospace;font-weight:700;font-size:0.88rem">
                {trend} {fmt_pct(perf)}
              </span>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            if st.button("View", key=f"lb_{i}_{m['name']}"):
                st.session_state["leaderboard_selected"] = m["name"]
                st.rerun()


# ── Tab: WATCHLIST ────────────────────────────────────────────────────────────

def render_watchlist():
    """Manually tracked tickers with live price and 7-day sparkline."""
    from memory import get_watchlist, add_to_watchlist, remove_from_watchlist

    st.markdown('<div style="font-size:1.1rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;color:#e2e8f0">👁 Watchlist</div>', unsafe_allow_html=True)

    col_input, col_add = st.columns([3, 1])
    with col_input:
        new_ticker = st.text_input(
            "Add ticker", placeholder="e.g. NVDA",
            key="wl_input", label_visibility="collapsed",
        )
    with col_add:
        if st.button("Add", width='stretch') and new_ticker:
            add_to_watchlist(new_ticker.upper().strip())
            st.rerun()

    st.markdown("---")
    watchlist = get_watchlist()

    if not watchlist:
        empty_state(
            "👁", "Your watchlist is empty",
            "Add tickers above, or click '+ Watchlist' on any signal card in the Feed."
        )
        return

    for ticker in watchlist:
        quote = get_ticker_quote(ticker)
        closes = get_sparkline_data(ticker)
        sparkline = make_sparkline_svg(closes)

        price_str = fmt_money(quote["price"]) if quote.get("price") else "—"
        chg = quote.get("change_pct")
        chg_html = ""
        if chg is not None:
            badge_cls = "badge-green" if chg >= 0 else "badge-red"
            chg_html = f'<span class="badge {badge_cls}">{fmt_pct(chg)}</span>'

        col_data, col_rm = st.columns([6, 1])
        with col_data:
            st.markdown(
                f'<div class="watch-card">'
                f'<span style="font-weight:700;min-width:60px">${ticker}</span>'
                f'<span style="font-family:Space Mono,monospace">{price_str}</span>'
                f'{chg_html}'
                f'{sparkline}'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_rm:
            if st.button("✕", key=f"wl_rm_{ticker}"):
                remove_from_watchlist(ticker)
                st.rerun()


# ── Tab: LOGS ─────────────────────────────────────────────────────────────────

def render_logs():
    """Changelog with trade stats summary, filter, and CSV export."""
    from memory import get_changelog, get_pending_signals

    st.markdown('<div style="font-size:1.1rem;font-weight:700;letter-spacing:-0.02em;margin-bottom:0.75rem;color:#e2e8f0">📋 Changelog</div>', unsafe_allow_html=True)

    # ── Trade stats ──
    signals = get_pending_signals()
    executed = [s for s in signals if s.get("status") == "approved"]
    skipped = [s for s in signals if s.get("status") == "skipped"]
    total_deployed = sum(s.get("position_usd", 0) for s in executed)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Trades Executed", len(executed))
    col_b.metric("Trades Skipped", len(skipped))
    col_c.metric("Total Deployed", fmt_money(total_deployed))

    st.markdown("---")

    entries = get_changelog()
    if not entries:
        changelog_path = os.path.join(os.path.dirname(__file__), "docs", "CHANGELOG.md")
        try:
            with open(changelog_path, "r", encoding="utf-8") as f:
                raw = f.read()
            entries = [
                line.strip()
                for line in raw.split("\n")
                if line.strip() and not line.startswith("#")
            ]
        except Exception:
            entries = []

    if not entries:
        empty_state(
            "📋", "No log entries yet",
            "Activity is recorded here automatically as the system runs — trades, vetoes, roster changes, errors."
        )
        return

    col_filter, col_export = st.columns([3, 1])
    with col_filter:
        filter_text = st.text_input(
            "Filter", placeholder="e.g. AAPL, EXECUTED, ROSTER",
            key="log_filter", label_visibility="collapsed",
        )
    with col_export:
        if st.button("⬇️ Export CSV", width='stretch'):
            df = pd.DataFrame({"entry": entries})
            st.download_button("Download", df.to_csv(index=False), "changelog.csv", "text/csv")

    filtered = [
        e for e in reversed(entries)
        if not filter_text or filter_text.upper() in e.upper()
    ]

    for entry in filtered[:200]:
        if "EXECUTED" in entry:
            color = "#00d4aa"
        elif "ERROR" in entry or "STOP_LOSS" in entry:
            color = "#ff4757"
        elif "SKIPPED" in entry or "VETO" in entry:
            color = "#475569"
        elif "ROSTER" in entry or "WEIGHT" in entry:
            color = "#a78bfa"
        elif "MODE CHANGE" in entry:
            color = "#ffa502"
        else:
            color = "#334155"

        st.markdown(
            f'<div style="font-family:Space Mono,monospace;font-size:0.75rem;'
            f'color:{color};padding:0.2rem 0;border-bottom:1px solid #0a0f1a">{entry}</div>',
            unsafe_allow_html=True,
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    """Entry point — start scheduler, render sidebar and 7-tab layout."""
    from scheduler import start_scheduler
    from memory import is_roster_initialized

    if "scheduler_started" not in st.session_state:
        start_scheduler()
        st.session_state["scheduler_started"] = True

    render_sidebar()

    # ── Mobile-friendly header ──
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;
                margin-bottom:0.25rem;padding-bottom:0.75rem;
                border-bottom:1px solid rgba(30,41,59,0.4)">
      <div style="display:flex;align-items:center;gap:0.6rem">
        <span style="font-size:1.5rem">🪞</span>
        <div>
          <span style="font-size:1.35rem;font-weight:700;letter-spacing:-0.03em">MIRROR AI</span>
          <span style="font-size:0.65rem;color:#475569;margin-left:0.4rem;
                       font-family:'Space Mono',monospace;vertical-align:middle">v2</span>
        </div>
      </div>
      <div style="font-family:'Space Mono',monospace;font-size:0.7rem;color:#334155;text-align:right">
        <span style="color:#00d4aa;font-size:0.65rem">● LIVE</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if not is_roster_initialized():
        st.info(
            "🔄 **Roster not yet bootstrapped.** "
            "At 7:30am ET on the first weekday run, the system will use Brave Search + AI to "
            "discover and rank the 10 best public figures to mirror. No names are hardcoded."
        )

    tabs = st.tabs([
        "📊 Dashboard",
        "📡 Feed",
        "💼 Positions",
        "👥 Roster",
        "🏆 Leaders",
        "👁 Watchlist",
        "📋 Logs",
    ])
    with tabs[0]: render_dashboard()
    with tabs[1]: render_feed()
    with tabs[2]: render_positions()
    with tabs[3]: render_roster()
    with tabs[4]: render_leaderboard()
    with tabs[5]: render_watchlist()
    with tabs[6]: render_logs()


if __name__ == "__main__":
    main()
