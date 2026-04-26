import streamlit as st
import json
import os
import requests as _req
from pathlib import Path
from datetime import datetime, timezone, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from knowledge import TICKER_PROFILES, TRADER_BIOS, SCORING_EXPLAINER, confidence_label

HERE = Path(__file__).parent

st.set_page_config(
    page_title="MIRROR AI",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600&display=swap');

:root {
  --bg:       #060608;
  --surface:  #0d0d10;
  --surface2: #13131a;
  --border:   #1c1c26;
  --border2:  #252535;
  --green:    #00e87a;
  --green2:   #00b85f;
  --red:      #ff3f5e;
  --amber:    #f5a623;
  --blue:     #4a9eff;
  --purple:   #9b6dff;
  --muted:    #3a3a50;
  --text:     #e2e2f0;
  --subtext:  #6e6e90;
  --mono:     'Space Mono', monospace;
  --sans:     'Inter', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: var(--sans) !important;
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

[data-testid="stAppViewContainer"] { padding-top: 0 !important; }
[data-testid="stMainBlockContainer"] { padding: 0 12px 80px !important; max-width: 540px !important; margin: 0 auto !important; }

/* ── metrics ── */
[data-testid="stMetricValue"] {
  font-family: var(--mono) !important;
  color: var(--green) !important;
  font-size: 1.25rem !important;
  font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
  color: var(--subtext) !important;
  font-size: 0.65rem !important;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--sans) !important;
}
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
[data-testid="metric-container"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 12px 14px !important;
}

/* ── buttons ── */
div.stButton > button {
  width: 100% !important;
  border-radius: 6px !important;
  font-family: var(--mono) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.06em !important;
  padding: 9px 8px !important;
  border: 1px solid var(--border2) !important;
  background: var(--surface2) !important;
  color: var(--subtext) !important;
  transition: all 0.15s ease !important;
  cursor: pointer !important;
}
div.stButton > button:hover {
  border-color: var(--green) !important;
  color: var(--green) !important;
  background: #00e87a10 !important;
}
div.stButton > button[kind="primary"] {
  background: #00e87a18 !important;
  border-color: var(--green) !important;
  color: var(--green) !important;
}

/* ── custom components ── */
.wordmark {
  font-family: var(--mono);
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 0.25em;
  color: var(--green);
  text-align: center;
  padding: 20px 0 2px;
}
.sub {
  font-size: 0.6rem;
  color: var(--muted);
  text-align: center;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  margin-bottom: 18px;
}
.divider {
  height: 1px;
  background: var(--border);
  margin: 14px 0;
}
.section-label {
  font-size: 0.6rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 20px 0 10px;
  padding-bottom: 7px;
  border-bottom: 1px solid var(--border);
  font-family: var(--mono);
}

/* ── signal card ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 10px;
  transition: border-color 0.15s;
}
.card:hover { border-color: var(--border2); }
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}
.ticker-wrap { display: flex; align-items: baseline; gap: 8px; }
.ticker {
  font-family: var(--mono);
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 0.04em;
}
.side-tag {
  font-family: var(--mono);
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  background: #00e87a14;
  border: 1px solid #00e87a30;
  color: var(--green);
  padding: 2px 6px;
  border-radius: 4px;
}
.side-sell {
  background: #ff3f5e14;
  border-color: #ff3f5e30;
  color: var(--red);
}
.score-badge {
  font-family: var(--mono);
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--green);
  background: #00e87a0a;
  border: 1px solid #00e87a20;
  border-radius: 6px;
  padding: 4px 10px;
  min-width: 52px;
  text-align: center;
}
.holder-pills { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
.pill {
  font-size: 0.6rem;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--subtext);
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 7px;
  font-family: var(--mono);
}
.bar-track { background: var(--border); border-radius: 2px; height: 2px; margin: 4px 0 10px; }
.bar-fill  { height: 2px; border-radius: 2px; background: var(--green); }
.bar-fill-amber  { background: var(--amber); }
.bar-fill-low    { background: var(--muted); }
.stats { display: flex; gap: 16px; }
.stat  { flex: 1; }
.stat-label { font-size: 0.6rem; color: var(--subtext); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px; }
.stat-val   { font-family: var(--mono); font-size: 0.8rem; color: var(--text); }

/* ── reviewed ── */
.card-done { opacity: 0.42; }
.badge-ok {
  font-family: var(--mono); font-size: 0.58rem; letter-spacing: 0.08em;
  background: #00e87a10; border: 1px solid var(--green); color: var(--green);
  border-radius: 4px; padding: 2px 7px;
}
.badge-no {
  font-family: var(--mono); font-size: 0.58rem; letter-spacing: 0.08em;
  background: #ff3f5e10; border: 1px solid var(--red); color: var(--red);
  border-radius: 4px; padding: 2px 7px;
}

/* ── positions ── */
.pos-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 11px 0; border-bottom: 1px solid var(--border);
}
.pos-sym { font-family: var(--mono); font-size: 0.95rem; color: var(--text); font-weight: 700; }
.pos-detail { font-size: 0.65rem; color: var(--subtext); margin-top: 2px; }
.pnl-pos { font-family: var(--mono); font-size: 0.8rem; color: var(--green); }
.pnl-neg { font-family: var(--mono); font-size: 0.8rem; color: var(--red); }

/* ── leaderboard ── */
.lb-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 10px; margin-bottom: 8px;
}
.lb-rank { font-family: var(--mono); font-size: 0.7rem; color: var(--muted); min-width: 24px; }
.lb-name { font-size: 0.82rem; color: var(--text); font-weight: 500; flex: 1; }
.lb-score { font-family: var(--mono); font-size: 0.78rem; color: var(--green); }

/* ── category tabs ── */
.cat-tab-row { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
.cat-tab {
  font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.1em;
  text-transform: uppercase; padding: 6px 12px; border-radius: 6px;
  border: 1px solid var(--border2); background: var(--surface2);
  color: var(--subtext); cursor: pointer; transition: all 0.15s;
}
.cat-tab-active {
  border-color: var(--green); background: #00e87a14; color: var(--green);
}

/* ── category accent colours ── */
.accent-pol  { --acc: var(--green); }
.accent-ceo  { --acc: var(--blue); }
.accent-ath  { --acc: var(--amber); }
.accent-sec  { --acc: var(--purple); }

/* ── empty state ── */
.empty {
  text-align: center; padding: 48px 20px;
  color: var(--muted); font-size: 0.78rem;
  font-family: var(--mono); letter-spacing: 0.05em; line-height: 1.8;
}

/* ── toast ── */
.toast-ok  { background:#00e87a14; border:1px solid var(--green); border-radius:8px; padding:10px 14px; font-size:0.75rem; color:var(--green); font-family:var(--mono); margin-bottom:8px; }
.toast-err { background:#ff3f5e14; border:1px solid var(--red);   border-radius:8px; padding:10px 14px; font-size:0.75rem; color:var(--red);   font-family:var(--mono); margin-bottom:8px; }

/* ── hide streamlit chrome ── */
#MainMenu, footer, [data-testid="stStatusWidget"] { display:none !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ALPACA
# ─────────────────────────────────────────────

DECISIONS_FILE = HERE / 'decisions.json'

def load_decisions():
    try:
        return json.load(open(DECISIONS_FILE))
    except Exception:
        return {}

def save_decisions(d):
    with open(DECISIONS_FILE, 'w') as f:
        json.dump(d, f)

@st.cache_resource
def get_client():
    k = os.getenv('ALPACA_KEY')
    s = os.getenv('ALPACA_SECRET')
    if not k or not s:
        return None
    return TradingClient(k, s, paper=True)

def get_trade_notional():
    """0.5% of current equity, minimum $10."""
    acct = load_account()
    if acct:
        return max(10.0, round(float(acct.equity) * 0.005, 2))
    return 500.0

def place_order(symbol):
    client = get_client()
    if not client:
        return False, "Alpaca credentials not configured", None
    notional = get_trade_notional()
    try:
        req = MarketOrderRequest(
            symbol=symbol, notional=notional,
            side=OrderSide.BUY, time_in_force=TimeInForce.DAY
        )
        order = client.submit_order(req)
        # Poll once for fill status (max 2s)
        import time as _t
        _t.sleep(1.5)
        try:
            o = client.get_order_by_id(order.id)
            status = str(o.status).split('.')[-1].lower()
        except Exception:
            status = 'submitted'
        return True, f"id {str(order.id)[:8]}  ·  {status}", notional
    except Exception as e:
        return False, str(e), None

@st.cache_data(ttl=60)
def load_account():
    client = get_client()
    if not client:
        return None
    try:
        return client.get_account()
    except Exception:
        return None

@st.cache_data(ttl=60)
def load_positions():
    client = get_client()
    if not client:
        return []
    try:
        return client.get_all_positions()
    except Exception:
        return []

@st.cache_data(ttl=3600)
def fetch_price_history(symbol):
    """30-day daily closes via Alpaca market data. Returns list of (date, close) or []."""
    key    = os.getenv('ALPACA_KEY', '')
    secret = os.getenv('ALPACA_SECRET', '')
    if not key:
        return []
    end   = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    start = (datetime.now(timezone.utc) - timedelta(days=45)).strftime('%Y-%m-%d')
    try:
        r = _req.get(
            f'https://data.alpaca.markets/v2/stocks/{symbol}/bars',
            params={'timeframe': '1Day', 'start': start, 'end': end, 'limit': 30, 'feed': 'iex'},
            headers={'APCA-API-KEY-ID': key, 'APCA-API-SECRET-KEY': secret},
            timeout=10,
        )
        if not r.ok:
            return []
        bars = r.json().get('bars', [])
        return [(b['t'][:10], round(b['c'], 2)) for b in bars]
    except Exception:
        return []


@st.cache_data(ttl=300)
def load_suggestions():
    try:
        with open(HERE / 'suggestions.json') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {'politicians': data, 'ceos': [], 'athletes': [], 'sectors': [], 'last_updated': None}
        return data
    except Exception:
        return {'politicians': [], 'ceos': [], 'athletes': [], 'sectors': [], 'last_updated': None}


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

for key, default in [
    ('tab', 'feed'),
    ('category', 'politicians'),
    ('toasts', []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if 'decisions' not in st.session_state:
    st.session_state.decisions = load_decisions()


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown('<div class="wordmark">MIRROR AI</div>', unsafe_allow_html=True)

# Freshness indicator
_sug = load_suggestions()
_lu  = _sug.get('last_updated')
if _lu:
    from datetime import datetime as _dt, timezone as _tz
    _age = _dt.now(_tz.utc) - _dt.fromisoformat(_lu)
    _h = int(_age.total_seconds() // 3600)
    _fresh = f"Updated {_h}h ago" if _h < 24 else f"Updated {_age.days}d ago"
else:
    _fresh = "No data yet — run fetcher.py"
st.markdown(f'<div class="sub">Paper trading &nbsp;·&nbsp; {_fresh}</div>', unsafe_allow_html=True)

account = load_account()
if account:
    equity      = float(account.equity)
    buying_pow  = float(account.buying_power)
    today_pnl   = equity - float(account.last_equity)
    pnl_delta   = f"{'▲' if today_pnl >= 0 else '▼'} ${abs(today_pnl):,.0f}"
    c1, c2, c3 = st.columns(3)
    c1.metric("Balance",       f"${equity:,.0f}")
    c2.metric("Buying Power",  f"${buying_pow:,.0f}")
    c3.metric("Today P&L",     f"${today_pnl:+,.0f}")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN NAVIGATION
# ─────────────────────────────────────────────

n1, n2, n3 = st.columns(3)
with n1:
    if st.button("FEED",       use_container_width=True, type="primary" if st.session_state.tab == 'feed'       else "secondary"):
        st.session_state.tab = 'feed';       st.rerun()
with n2:
    if st.button("POSITIONS",  use_container_width=True, type="primary" if st.session_state.tab == 'positions'  else "secondary"):
        st.session_state.tab = 'positions';  st.rerun()
with n3:
    if st.button("LEADERBOARD",use_container_width=True, type="primary" if st.session_state.tab == 'leaderboard' else "secondary"):
        st.session_state.tab = 'leaderboard'; st.rerun()


# ─────────────────────────────────────────────
# TOASTS
# ─────────────────────────────────────────────

for ok, msg in st.session_state.toasts:
    cls = 'toast-ok' if ok else 'toast-err'
    st.markdown(f'<div class="{cls}">{msg}</div>', unsafe_allow_html=True)
st.session_state.toasts = []


# ─────────────────────────────────────────────
# FEED TAB
# ─────────────────────────────────────────────

CATEGORIES = {
    'politicians': {'label': 'Politicians', 'accent': '#00e87a', 'count': 7},
    'ceos':        {'label': 'Superinvestors', 'accent': '#4a9eff', 'count': 7},
    'athletes':    {'label': 'Athletes',    'accent': '#f5a623', 'count': 7},
    'sectors':     {'label': 'Sectors',     'accent': '#9b6dff', 'count': 7},
}

if st.session_state.tab == 'feed':
    all_suggestions = load_suggestions()

    # Category selector
    cat_cols = st.columns(4)
    for i, (cat_key, cat_info) in enumerate(CATEGORIES.items()):
        with cat_cols[i]:
            is_active = st.session_state.category == cat_key
            if st.button(
                cat_info['label'],
                key=f"cat_{cat_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.category = cat_key
                st.rerun()

    cat = st.session_state.category
    accent = CATEGORIES[cat]['accent']
    suggestions = all_suggestions.get(cat, [])

    pending = [s for s in suggestions if st.session_state.decisions.get(f"{cat}_{s['ticker']}", 'pending') == 'pending']
    decided = [s for s in suggestions if st.session_state.decisions.get(f"{cat}_{s['ticker']}", 'pending') != 'pending']

    if not pending and not decided:
        st.markdown('<div class="empty">No signals available<br>Run fetcher.py to pull latest data</div>', unsafe_allow_html=True)
    elif not pending:
        st.markdown('<div class="empty">All signals reviewed<br>Check back after next data refresh</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-label">{len(pending)} pending &nbsp;·&nbsp; {cat.upper()}</div>', unsafe_allow_html=True)

    for s in pending:
        ticker     = s.get('ticker', '')
        score      = float(s.get('score', 0))
        conviction = int(s.get('conviction', 1))
        investors  = s.get('investors', '')
        buy_count  = int(s.get('buy_count', conviction))
        total      = CATEGORIES[cat]['count']
        bar_pct    = min(100, int((conviction / total) * 100))
        conf_label, conf_color = confidence_label(conviction, total, score)

        pills = ''.join(f'<span class="pill">{p.strip()}</span>' for p in investors.split(',') if p.strip())
        profile = TICKER_PROFILES.get(ticker, {})

        st.markdown(f"""
        <div class="card">
          <div class="card-top">
            <div class="ticker-wrap">
              <span class="ticker" style="color:{accent}">{ticker}</span>
              <span class="side-tag">BUY</span>
              <span style="font-size:0.58rem;font-family:var(--mono);color:{conf_color};background:{conf_color}14;border:1px solid {conf_color}40;border-radius:3px;padding:2px 6px">{conf_label}</span>
            </div>
            <span class="score-badge" style="color:{accent};border-color:{accent}33;background:{accent}0a">{score:.2f}</span>
          </div>
          {f'<div style="font-size:0.72rem;color:var(--subtext);margin-bottom:8px">{profile.get("company","")} &nbsp;·&nbsp; {profile.get("sector","")}</div>' if profile else ''}
          <div class="holder-pills">{pills}</div>
          <div class="bar-track"><div style="height:2px;border-radius:2px;background:{accent};width:{bar_pct}%"></div></div>
          <div class="stats">
            <div class="stat"><div class="stat-label">Conviction</div><div class="stat-val">{conviction} / {total}</div></div>
            <div class="stat"><div class="stat-label">Disclosures</div><div class="stat-val">{buy_count}</div></div>
            <div class="stat"><div class="stat-label">Signal</div><div class="stat-val">{score:.1f}</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── DETAIL EXPANDER ──
        with st.expander(f"  DEEP DIVE  {ticker}", expanded=False):
            # Price chart
            bars = fetch_price_history(ticker)
            if bars:
                closes = [b[1] for b in bars]
                dates  = [b[0] for b in bars]
                pct_chg = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] else 0
                chg_col = '#00e87a' if pct_chg >= 0 else '#ff3f5e'
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
                  <span style="font-family:var(--mono);font-size:1.1rem;color:{accent}">${closes[-1]:,.2f}</span>
                  <span style="font-family:var(--mono);font-size:0.8rem;color:{chg_col}">{pct_chg:+.1f}% · 30d</span>
                </div>""", unsafe_allow_html=True)
                st.line_chart(
                    data={'Price': closes},
                    height=120,
                    use_container_width=True,
                )
            else:
                st.markdown('<div style="font-size:0.72rem;color:var(--subtext);margin-bottom:8px">Price history unavailable</div>', unsafe_allow_html=True)

            # Ticker profile
            if profile:
                st.markdown(f"""
                <div style="margin:12px 0 8px">
                  <div style="font-size:0.6rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:6px">ABOUT {ticker}</div>
                  <div style="font-size:0.78rem;color:var(--text);line-height:1.6">{profile.get('summary','')}</div>
                  <div style="margin-top:6px;font-size:0.65rem;color:var(--subtext)">Risk level: {'▪' * profile.get('risk',3)}{'▫' * (5 - profile.get('risk',3))} {profile.get('risk',3)}/5</div>
                </div>""", unsafe_allow_html=True)

            # Trader bios
            trader_list = [p.strip() for p in investors.split(',') if p.strip()]
            if trader_list:
                st.markdown('<div style="font-size:0.6rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin:12px 0 6px">WHO BOUGHT IT</div>', unsafe_allow_html=True)
                for trader in trader_list:
                    bio = TRADER_BIOS.get(trader, {})
                    if bio:
                        st.markdown(f"""
                        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:8px">
                          <div style="font-size:0.82rem;font-weight:600;color:var(--text);margin-bottom:2px">{trader}</div>
                          <div style="font-size:0.65rem;color:var(--subtext);margin-bottom:6px">{bio.get('role','')}</div>
                          <div style="font-size:0.7rem;color:var(--text);line-height:1.5;margin-bottom:4px"><strong>Track record:</strong> {bio.get('track_record','')}</div>
                          <div style="font-size:0.7rem;color:var(--text);line-height:1.5;margin-bottom:4px"><strong>Style:</strong> {bio.get('style','')}</div>
                          <div style="font-size:0.7rem;color:var(--subtext);line-height:1.5"><strong>Notable:</strong> {bio.get('notable','')}</div>
                        </div>""", unsafe_allow_html=True)

            # AI reasoning
            reasoning = SCORING_EXPLAINER.get(cat, '')
            if reasoning:
                st.markdown(f"""
                <div style="background:#00e87a08;border:1px solid #00e87a20;border-radius:8px;padding:12px;margin-top:8px">
                  <div style="font-size:0.6rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--green);margin-bottom:6px">WHY MIRROR AI PICKED THIS</div>
                  <div style="font-size:0.72rem;color:var(--subtext);line-height:1.6">{reasoning}</div>
                  <div style="margin-top:8px;font-size:0.7rem;color:var(--text)">
                    Confidence: <span style="color:{conf_color};font-family:var(--mono)">{conf_label}</span> &nbsp;·&nbsp;
                    Score: <span style="font-family:var(--mono);color:{accent}">{score:.2f}</span> &nbsp;·&nbsp;
                    {conviction} of {total} holders bought
                  </div>
                </div>""", unsafe_allow_html=True)

        btn_a, btn_r = st.columns([3, 2])
        with btn_a:
            notional_preview = get_trade_notional()
            if st.button(f"APPROVE  ${notional_preview:,.0f}", key=f"approve_{cat}_{ticker}", use_container_width=True):
                ok, result, notional = place_order(ticker)
                st.session_state.decisions[f"{cat}_{ticker}"] = 'approved'
                save_decisions(st.session_state.decisions)
                if ok:
                    st.session_state.toasts.append((True, f"Order placed: {ticker}  ·  ${notional:,.2f}  ·  {result}"))
                else:
                    st.session_state.toasts.append((False, f"Order failed for {ticker}: {result}"))
                st.rerun()
        with btn_r:
            if st.button("REJECT", key=f"reject_{cat}_{ticker}", use_container_width=True):
                st.session_state.decisions[f"{cat}_{ticker}"] = 'rejected'
                save_decisions(st.session_state.decisions)
                st.rerun()

    if decided:
        st.markdown(f'<div class="section-label">{len(decided)} reviewed</div>', unsafe_allow_html=True)
        for s in decided:
            ticker   = s.get('ticker', '')
            decision = st.session_state.decisions.get(f"{cat}_{ticker}", '')
            badge    = f'<span class="badge-ok">APPROVED</span>' if decision == 'approved' else '<span class="badge-no">REJECTED</span>'
            st.markdown(f"""
            <div class="card card-done">
              <div class="card-top">
                <span class="ticker" style="color:{accent};font-size:1rem">{ticker}</span>
                {badge}
              </div>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# POSITIONS TAB
# ─────────────────────────────────────────────

elif st.session_state.tab == 'positions':
    positions = load_positions()
    if not positions:
        st.markdown('<div class="empty">No open positions<br>Approve signals in the Feed to place trades</div>', unsafe_allow_html=True)
    else:
        total_pnl = sum(float(p.unrealized_pl) for p in positions)
        pnl_cls   = 'pnl-pos' if total_pnl >= 0 else 'pnl-neg'
        st.markdown(f'<div class="section-label">Open positions &nbsp;·&nbsp; Unrealized P&amp;L <span class="{pnl_cls}">${total_pnl:+,.2f}</span></div>', unsafe_allow_html=True)

        for p in sorted(positions, key=lambda x: float(x.unrealized_pl), reverse=True):
            pnl = float(p.unrealized_pl)
            pct = float(p.unrealized_plpc) * 100
            cls = 'pnl-pos' if pnl >= 0 else 'pnl-neg'
            st.markdown(f"""
            <div class="pos-row">
              <div>
                <div class="pos-sym">{p.symbol}</div>
                <div class="pos-detail">{float(p.qty):.4f} shares &nbsp;·&nbsp; ${float(p.current_price):,.2f}</div>
              </div>
              <div style="text-align:right">
                <div class="{cls}">${pnl:+,.2f}</div>
                <div class="{cls}" style="font-size:0.68rem">{pct:+.2f}%</div>
              </div>
            </div>""", unsafe_allow_html=True)

        if st.button("REFRESH POSITIONS", use_container_width=True):
            st.cache_data.clear()
            st.rerun()


# ─────────────────────────────────────────────
# LEADERBOARD TAB
# ─────────────────────────────────────────────

elif st.session_state.tab == 'leaderboard':
    all_suggestions = load_suggestions()

    for cat_key, cat_info in CATEGORIES.items():
        accent      = cat_info['accent']
        suggestions = all_suggestions.get(cat_key, [])
        if not suggestions:
            continue

        # Aggregate score per investor/holder
        holder_scores: dict = {}
        for s in suggestions:
            for inv in s.get('investors', '').split(','):
                inv = inv.strip()
                if inv:
                    holder_scores[inv] = holder_scores.get(inv, 0) + float(s.get('score', 0))

        ranked    = sorted(holder_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = ranked[0][1] if ranked else 1

        st.markdown(f'<div class="section-label" style="border-color:{accent}30">{cat_info["label"].upper()}</div>', unsafe_allow_html=True)

        for i, (name, score) in enumerate(ranked[:7]):
            bar_pct = int((score / max_score) * 100)
            st.markdown(f"""
            <div class="lb-row" style="border-color:{accent}18">
              <span class="lb-rank">{str(i+1).zfill(2)}</span>
              <div style="flex:1">
                <div class="lb-name">{name}</div>
                <div class="bar-track" style="margin:4px 0 0"><div style="height:2px;border-radius:2px;background:{accent};width:{bar_pct}%"></div></div>
              </div>
              <span class="lb-score" style="color:{accent}">{score:.1f}</span>
            </div>""", unsafe_allow_html=True)

    if st.button("REFRESH ALL DATA", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
