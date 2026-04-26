import streamlit as st
import json
import os
import requests as _req
from pathlib import Path
from datetime import datetime, timezone, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from knowledge import TICKER_PROFILES, TICKER_DOMAIN, TRADER_BIOS, SCORING_EXPLAINER, confidence_label

HERE = Path(__file__).parent

st.set_page_config(
    page_title="MIRROR AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root {
  --bg:      #04080f;
  --surface: #080e1c;
  --card:    #0b1222;
  --glass:   rgba(255,255,255,0.025);
  --border:  rgba(255,255,255,0.06);
  --border2: rgba(255,255,255,0.11);
  --green:   #00d4aa;
  --red:     #ff4757;
  --amber:   #ffa502;
  --blue:    #38bdf8;
  --purple:  #a78bfa;
  --gold:    #fbbf24;
  --text:    #e2e8f0;
  --sub:     #7c8fad;
  --muted:   #3a4a62;
  --mono:    'Space Mono', monospace;
  --sans:    'Space Grotesk', sans-serif;
}

html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: var(--sans) !important;
  color: var(--text) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
  min-width: 240px !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

/* ── Hide Streamlit chrome ── */
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], #MainMenu, footer { display: none !important; }

/* ── Main padding ── */
[data-testid="stMainBlockContainer"] {
  padding: 20px 28px 80px !important;
  max-width: 860px !important;
}

/* ── Metric tiles ── */
[data-testid="metric-container"] {
  background: var(--glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 14px 18px !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--mono) !important;
  font-size: 1.25rem !important;
  font-weight: 700 !important;
  color: var(--green) !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.58rem !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--sub) !important;
}

/* ── Buttons ── */
div.stButton > button {
  width: 100% !important;
  border-radius: 8px !important;
  font-family: var(--mono) !important;
  font-size: 0.7rem !important;
  letter-spacing: 0.07em !important;
  padding: 10px 14px !important;
  border: 1px solid var(--border2) !important;
  background: var(--glass) !important;
  color: var(--sub) !important;
  transition: all 0.18s ease !important;
}
div.stButton > button:hover {
  border-color: var(--green) !important;
  color: var(--green) !important;
  background: rgba(0,212,170,0.07) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 18px rgba(0,212,170,0.12) !important;
}
div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg,rgba(0,212,170,0.13),rgba(56,189,248,0.09)) !important;
  border-color: var(--green) !important;
  color: var(--green) !important;
}

/* ── Slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
  background: var(--green) !important;
  border-color: var(--green) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
  background: rgba(255,255,255,0.015) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  margin-top: -6px !important;
  margin-bottom: 10px !important;
}
[data-testid="stExpander"] summary {
  font-family: var(--mono) !important;
  font-size: 0.66rem !important;
  letter-spacing: 0.09em !important;
  color: var(--sub) !important;
}

/* ─── Named CSS classes used in render_signal_card ─── */

.wordmark {
  font-family: var(--mono); font-size: 1.05rem; font-weight: 700;
  letter-spacing: 0.28em;
  background: linear-gradient(90deg, var(--green), var(--blue));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  padding: 22px 20px 2px; text-align: center;
}
.sub-tag {
  font-size: 0.56rem; color: var(--muted); text-align: center;
  letter-spacing: 0.18em; text-transform: uppercase;
  margin-bottom: 20px; font-family: var(--sans);
}
.nav-section {
  font-size: 0.53rem; letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--muted); padding: 14px 18px 6px; font-family: var(--mono);
}
.section-label {
  font-size: 0.58rem; letter-spacing: 0.17em; text-transform: uppercase;
  color: var(--muted); margin: 18px 0 10px;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
  font-family: var(--mono);
}

/* Signal card shell */
.card {
  background: linear-gradient(160deg, var(--card) 0%, #06101f 100%);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px 18px 12px;
  margin-bottom: 0px;
  position: relative; overflow: hidden;
  transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
}
.card:hover {
  border-color: var(--border2);
  transform: translateY(-2px);
  box-shadow: 0 10px 36px rgba(0,0,0,0.35);
}
.card::before {
  content:''; position:absolute; top:0; left:0; right:0; height:1px;
  background: linear-gradient(90deg, transparent, var(--border2), transparent);
}
.card-sell { border-color: rgba(255,71,87,0.18) !important; }
.card-sell::before { background: linear-gradient(90deg, transparent, rgba(255,71,87,0.28), transparent) !important; }

/* Card header row */
.card-header { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
.card-left  { display:flex; align-items:center; gap:12px; flex:1; min-width:0; }
.logo-wrap  {
  width:40px; height:40px; border-radius:10px;
  background:var(--glass); border:1px solid var(--border);
  display:flex; align-items:center; justify-content:center;
  overflow:hidden; flex-shrink:0;
}
.logo-wrap img { width:28px; height:28px; object-fit:contain; border-radius:4px; }
.logo-fallback { font-family:var(--mono); font-size:0.7rem; color:var(--sub); font-weight:700; }
.ticker-block {}
.ticker { font-family:var(--mono); font-size:1.2rem; font-weight:700; letter-spacing:0.03em; line-height:1.1; }
.company-name { font-size:0.67rem; color:var(--sub); margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

/* Score ring */
.score-ring {
  font-family:var(--mono); font-size:0.95rem; font-weight:700;
  width:48px; height:48px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  border:2px solid; flex-shrink:0;
}

/* Badges */
.badges { display:flex; gap:5px; flex-wrap:wrap; margin:8px 0 6px; }
.badge {
  font-family:var(--mono); font-size:0.56rem; letter-spacing:0.08em;
  padding:2px 7px; border-radius:4px; border:1px solid;
}
.badge-buy    { background:rgba(0,212,170,0.1);  border-color:rgba(0,212,170,0.28); color:var(--green); }
.badge-sell   { background:rgba(255,71,87,0.1);  border-color:rgba(255,71,87,0.28); color:var(--red); }
.badge-high   { background:rgba(0,212,170,0.08); border-color:rgba(0,212,170,0.22); color:var(--green); }
.badge-medium { background:rgba(255,165,2,0.08); border-color:rgba(255,165,2,0.22); color:var(--amber); }
.badge-low    { background:rgba(124,143,173,0.08);border-color:rgba(124,143,173,0.18);color:var(--sub); }

/* Investor pills */
.pills { display:flex; flex-wrap:wrap; gap:4px; margin:6px 0 8px; }
.pill {
  font-size:0.59rem; letter-spacing:0.06em;
  color:var(--sub); background:rgba(255,255,255,0.03);
  border:1px solid var(--border); border-radius:4px;
  padding:2px 7px; font-family:var(--mono);
}

/* Conviction bar */
.bar-track { background:var(--border); border-radius:3px; height:2px; margin:6px 0 10px; }

/* Stats row */
.stats { display:flex; gap:20px; margin-bottom:4px; }
.stat-label { font-size:0.56rem; color:var(--muted); letter-spacing:0.09em; text-transform:uppercase; margin-bottom:2px; }
.stat-val   { font-family:var(--mono); font-size:0.82rem; color:var(--text); }

/* Reviewed */
.card-done { opacity:0.3; }
.badge-mirrored { font-family:var(--mono); font-size:0.56rem; padding:2px 7px; border-radius:4px; background:rgba(0,212,170,0.08); border:1px solid var(--green); color:var(--green); }
.badge-skipped  { font-family:var(--mono); font-size:0.56rem; padding:2px 7px; border-radius:4px; background:rgba(255,71,87,0.08);  border:1px solid var(--red);   color:var(--red); }

/* Toasts */
.toast-ok  { background:rgba(0,212,170,0.07); border:1px solid rgba(0,212,170,0.28); border-radius:10px; padding:9px 15px; font-size:0.72rem; color:var(--green); font-family:var(--mono); margin-bottom:7px; }
.toast-err { background:rgba(255,71,87,0.07);  border:1px solid rgba(255,71,87,0.28);  border-radius:10px; padding:9px 15px; font-size:0.72rem; color:var(--red);   font-family:var(--mono); margin-bottom:7px; }

/* Deep dive */
.dd-label { font-size:0.55rem; letter-spacing:0.17em; text-transform:uppercase; color:var(--muted); margin:14px 0 7px; font-family:var(--mono); }
.bio-card { background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:10px; padding:12px 15px; margin-bottom:7px; }
.bio-name { font-size:0.85rem; font-weight:600; color:var(--text); margin-bottom:1px; }
.bio-role { font-size:0.62rem; color:var(--sub); margin-bottom:7px; }
.bio-line { font-size:0.69rem; color:var(--sub); line-height:1.65; margin-bottom:3px; }
.bio-line strong { color:var(--text); }
.ai-box {
  background:linear-gradient(135deg,rgba(0,212,170,0.04),rgba(56,189,248,0.03));
  border:1px solid rgba(0,212,170,0.14); border-radius:10px; padding:13px 15px; margin-top:10px;
}
.ai-label { font-size:0.55rem; letter-spacing:0.17em; text-transform:uppercase; color:var(--green); margin-bottom:7px; font-family:var(--mono); }
.ai-text  { font-size:0.7rem; color:var(--sub); line-height:1.72; }
.ai-summary { font-size:0.68rem; color:var(--text); margin-top:7px; font-family:var(--mono); }

/* Positions */
.pos-row { display:flex; justify-content:space-between; align-items:center; padding:13px 0; border-bottom:1px solid var(--border); }
.pos-sym  { font-family:var(--mono); font-size:0.98rem; font-weight:700; }
.pos-meta { font-size:0.62rem; color:var(--sub); margin-top:3px; }

/* Leaderboard */
.lb-row {
  display:flex; align-items:center; gap:12px;
  background:var(--glass); border:1px solid var(--border);
  border-radius:12px; padding:11px 15px; margin-bottom:7px;
  transition:border-color 0.15s;
}
.lb-row:hover { border-color:var(--border2); }
.lb-rank { font-family:var(--mono); font-size:0.68rem; color:var(--muted); min-width:26px; }
.lb-name { font-size:0.82rem; font-weight:500; color:var(--text); flex:1; }
.lb-score { font-family:var(--mono); font-size:0.8rem; }

/* Sidebar portfolio card */
.port-card {
  margin:0 14px 16px;
  background:rgba(255,255,255,0.025);
  border:1px solid var(--border);
  border-radius:12px; padding:14px 16px;
}
.port-label { font-size:0.55rem; letter-spacing:0.15em; text-transform:uppercase; color:var(--muted); margin-bottom:8px; font-family:var(--mono); }
.port-equity { font-family:var(--mono); font-size:1.35rem; font-weight:700; color:var(--green); margin-bottom:6px; }
.port-row { display:flex; justify-content:space-between; font-size:0.65rem; margin-top:4px; }
.port-key { color:var(--sub); }
.port-val { font-family:var(--mono); color:var(--text); }

.empty { text-align:center; padding:56px 20px; color:var(--muted); font-size:0.76rem; font-family:var(--mono); letter-spacing:0.05em; line-height:2.2; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
CATEGORIES = {
    'politicians': {'label': 'Politicians',    'accent': '#00d4aa', 'count': 8},
    'ceos':        {'label': 'Superinvestors', 'accent': '#38bdf8', 'count': 7},
    'athletes':    {'label': 'Athletes',       'accent': '#ffa502', 'count': 7},
    'sectors':     {'label': 'Sectors',        'accent': '#a78bfa', 'count': 7},
}

DECISIONS_FILE = HERE / 'decisions.json'
TRADE_LOG_FILE = HERE / 'trade_log.json'

# ─────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────
def load_decisions():
    try:
        return json.load(open(DECISIONS_FILE))
    except Exception:
        return {}

def save_decisions(d):
    with open(DECISIONS_FILE, 'w') as f:
        json.dump(d, f)

def load_trade_log():
    try:
        return json.load(open(TRADE_LOG_FILE))
    except Exception:
        return []

def append_trade_log(entry):
    log = load_trade_log()
    log.append(entry)
    with open(TRADE_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

@st.cache_data(ttl=300)
def load_suggestions():
    try:
        data = json.load(open(HERE / 'suggestions.json'))
        if isinstance(data, list):
            return {'politicians': data, 'ceos': [], 'athletes': [], 'sectors': [], 'last_updated': None}
        return data
    except Exception:
        return {'politicians': [], 'ceos': [], 'athletes': [], 'sectors': [], 'last_updated': None}

@st.cache_data(ttl=3600)
def fetch_price_history(symbol):
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
        return [(b['t'][:10], round(b['c'], 2)) for b in r.json().get('bars', [])]
    except Exception:
        return []

def logo_url(ticker):
    domain = TICKER_DOMAIN.get(ticker, '')
    if domain:
        return f'https://logo.clearbit.com/{domain}'
    return ''

# ─────────────────────────────────────────────
# ALPACA
# ─────────────────────────────────────────────
@st.cache_resource
def get_client():
    k = os.getenv('ALPACA_KEY')
    s = os.getenv('ALPACA_SECRET')
    if not k or not s:
        return None
    return TradingClient(k, s, paper=True)

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

def get_trade_notional(trade_pct=None):
    if trade_pct is None:
        trade_pct = st.session_state.get('trade_pct', 0.5)
    acct = load_account()
    if acct:
        equity = float(acct.equity)
        return max(10.0, round(equity * trade_pct / 100.0, 2))
    return round(trade_pct * 1000, 2)  # fallback: pretend $100k * pct

def place_order(symbol, side=OrderSide.BUY, category='', investors=''):
    client = get_client()
    if not client:
        return False, "Alpaca credentials not configured", None
    notional = get_trade_notional()
    try:
        if side == OrderSide.SELL:
            positions = load_positions()
            pos = next((p for p in positions if p.symbol == symbol), None)
            if not pos:
                return False, f"No open position in {symbol}", None
            req = MarketOrderRequest(
                symbol=symbol, qty=float(pos.qty),
                side=OrderSide.SELL, time_in_force=TimeInForce.DAY,
            )
        else:
            req = MarketOrderRequest(
                symbol=symbol, notional=notional,
                side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
            )
        order = client.submit_order(req)
        import time as _t; _t.sleep(1.5)
        try:
            o = client.get_order_by_id(order.id)
            status = str(o.status).split('.')[-1].lower()
        except Exception:
            status = 'submitted'
        append_trade_log({
            'ticker': symbol, 'side': 'sell' if side == OrderSide.SELL else 'buy',
            'category': category, 'investors': investors,
            'notional': notional, 'order_id': str(order.id),
            'status': status, 'timestamp': datetime.now(timezone.utc).isoformat(),
        })
        return True, f"id {str(order.id)[:8]}  ·  {status}", notional
    except Exception as e:
        return False, str(e), None

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in [('tab', 'feed'), ('category', 'politicians'), ('toasts', []), ('trade_pct', 0.5)]:
    if k not in st.session_state:
        st.session_state[k] = v
if 'decisions' not in st.session_state:
    st.session_state.decisions = load_decisions()

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30 * 60 * 1000, key="ar")
except ImportError:
    pass

# Compute notional ONCE at render time so button labels are consistent
_notional_now = get_trade_notional()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="wordmark">MIRROR AI</div>', unsafe_allow_html=True)

    sug   = load_suggestions()
    lu    = sug.get('last_updated')
    fresh = 'No data'
    if lu:
        try:
            age   = datetime.now(timezone.utc) - datetime.fromisoformat(lu)
            h     = int(age.total_seconds() // 3600)
            fresh = f"Updated {h}h ago" if h < 24 else f"Updated {age.days}d ago"
        except Exception:
            fresh = 'Timestamp error'
    st.markdown(f'<div class="sub-tag">{fresh}</div>', unsafe_allow_html=True)

    acct = load_account()
    if acct:
        eq  = float(acct.equity)
        bp  = float(acct.buying_power)
        pnl = eq - float(acct.last_equity)
        pnl_color = 'var(--green)' if pnl >= 0 else 'var(--red)'
        st.markdown(f"""<div class="port-card">
  <div class="port-label">Portfolio</div>
  <div class="port-equity">${eq:,.0f}</div>
  <div class="port-row"><span class="port-key">Buying power</span><span class="port-val">${bp:,.0f}</span></div>
  <div class="port-row"><span class="port-key">Today</span><span style="font-family:var(--mono);color:{pnl_color}">${pnl:+,.2f}</span></div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="nav-section">Navigate</div>', unsafe_allow_html=True)
    for tab_key, tab_label in [('feed', 'Signal Feed'), ('positions', 'Positions'), ('leaderboard', 'Leaderboard')]:
        is_active = st.session_state.tab == tab_key
        if st.button(tab_label, key=f"nav_{tab_key}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.tab = tab_key
            st.rerun()

    if st.session_state.tab == 'feed':
        st.markdown('<div class="nav-section">Category</div>', unsafe_allow_html=True)
        for cat_key, cat_info in CATEGORIES.items():
            is_active = st.session_state.category == cat_key
            if st.button(cat_info['label'], key=f"cat_{cat_key}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.category = cat_key
                st.rerun()

    st.markdown('<div class="nav-section">Trade size</div>', unsafe_allow_html=True)
    trade_pct = st.slider(
        "Trade pct", min_value=0.1, max_value=5.0,
        value=float(st.session_state.trade_pct),
        step=0.1, format="%.1f%%",
        label_visibility="collapsed",
    )
    st.session_state.trade_pct = trade_pct
    _notional_now = get_trade_notional(trade_pct)  # update after slider interaction
    st.markdown(
        f'<div style="font-size:0.62rem;color:var(--sub);text-align:center;margin-top:3px;font-family:var(--mono)">'
        f'≈ ${_notional_now:,.2f} per trade</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button("Refresh data", key="clear_cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────
# TOASTS
# ─────────────────────────────────────────────
for ok, msg in st.session_state.toasts:
    cls = "toast-ok" if ok else "toast-err"
    st.markdown(f'<div class="{cls}">{msg}</div>', unsafe_allow_html=True)
st.session_state.toasts = []

# ─────────────────────────────────────────────
# SIGNAL CARD RENDERER
# ─────────────────────────────────────────────
def render_signal_card(s, cat, accent, key_prefix, notional_now):
    ticker     = s.get('ticker', '')
    score      = float(s.get('score', 0))
    conviction = int(s.get('conviction', 1))
    investors  = s.get('investors', '')
    buy_count  = int(s.get('buy_count', conviction))
    action     = s.get('action', 'BUY')
    is_sell    = action == 'SELL'
    total      = CATEGORIES[cat]['count']
    bar_pct    = min(100, int((conviction / total) * 100))
    conf_lbl, conf_color = confidence_label(conviction, total, score)
    profile    = TICKER_PROFILES.get(ticker, {})
    data_as_of = s.get('data_as_of', '')
    ring_color = 'var(--red)' if is_sell else accent

    # ── Logo HTML
    lurl = logo_url(ticker)
    if lurl:
        logo_html = (
            f'<div class="logo-wrap">'
            f'<img src="{lurl}" onerror="this.style.display=\'none\';this.nextSibling.style.display=\'flex\'" alt="">'
            f'<span class="logo-fallback" style="display:none">{ticker[:2]}</span>'
            f'</div>'
        )
    else:
        logo_html = f'<div class="logo-wrap"><span class="logo-fallback">{ticker[:2]}</span></div>'

    # ── Badges
    badge_action = f'<span class="badge badge-{"sell" if is_sell else "buy"}">{action}</span>'
    badge_conf   = f'<span class="badge badge-{conf_lbl.lower()}">{conf_lbl}</span>'
    co_name      = profile.get('company', '') or ''
    sector_str   = profile.get('sector', '') or ''
    company_line = f'{co_name}{"  ·  " + sector_str if sector_str else ""}'

    # ── Investor pills
    inv_list = [p.strip() for p in investors.split(',') if p.strip()]
    pills_html = ''.join(f'<span class="pill">{p}</span>' for p in inv_list)

    # ── Stats
    stats_html = f"""
    <div class="stats">
      <div><div class="stat-label">Conviction</div><div class="stat-val">{conviction}/{total}</div></div>
      <div><div class="stat-label">Disclosures</div><div class="stat-val">{buy_count}</div></div>
      <div><div class="stat-label">Score</div><div class="stat-val" style="color:{ring_color}">{score:.2f}</div></div>
    </div>"""

    data_line = f'<div style="font-size:0.58rem;color:var(--muted);margin-top:2px">as of {data_as_of}</div>' if data_as_of else ''

    # Render card as two separate markdown blocks to avoid Streamlit HTML truncation
    st.markdown(f"""
<div class="card {'card-sell' if is_sell else ''}">
  <div class="card-header">
    <div class="card-left">
      {logo_html}
      <div class="ticker-block">
        <div class="ticker" style="color:{ring_color}">{ticker}</div>
        <div class="company-name">{company_line}</div>
        {data_line}
      </div>
    </div>
    <div class="score-ring" style="color:{ring_color};border-color:{ring_color}30;background:{ring_color}07">
      {score:.1f}
    </div>
  </div>
  <div class="badges">{badge_action} {badge_conf}</div>
  <div class="pills">{pills_html}</div>
  <div class="bar-track">
    <div style="height:2px;border-radius:3px;background:{ring_color};width:{bar_pct}%;opacity:0.75"></div>
  </div>
  {stats_html}
</div>
""", unsafe_allow_html=True)

    # ── Deep dive expander (separate from card HTML)
    with st.expander(f"Deep dive  {ticker}", expanded=False):
        bars = fetch_price_history(ticker)
        if bars:
            closes  = [b[1] for b in bars]
            pct_chg = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] else 0
            chg_col = '#00d4aa' if pct_chg >= 0 else '#ff4757'
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">'
                f'<span style="font-family:var(--mono);font-size:1.05rem;font-weight:700;color:{accent}">${closes[-1]:,.2f}</span>'
                f'<span style="font-family:var(--mono);font-size:0.75rem;color:{chg_col}">{pct_chg:+.1f}%  30d</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.line_chart({'Price': closes}, height=95, use_container_width=True)
        else:
            st.markdown('<div style="font-size:0.68rem;color:var(--sub);padding:6px 0">Price history unavailable</div>', unsafe_allow_html=True)

        if profile:
            risk = profile.get('risk', 3)
            st.markdown(
                f'<div class="dd-label">About {ticker}</div>'
                f'<div style="font-size:0.72rem;color:var(--text);line-height:1.72;margin-bottom:6px">{profile.get("summary","")}</div>'
                f'<div style="font-size:0.62rem;color:var(--sub)">Risk &nbsp;'
                f'<span style="font-family:var(--mono);color:var(--text)">{"█" * risk}{"░" * (5-risk)}</span>'
                f'&nbsp; {risk}/5</div>',
                unsafe_allow_html=True,
            )

        if inv_list:
            st.markdown('<div class="dd-label">Who is behind this signal</div>', unsafe_allow_html=True)
            for trader in inv_list:
                bio = TRADER_BIOS.get(trader, {})
                if bio:
                    st.markdown(
                        f'<div class="bio-card">'
                        f'<div class="bio-name">{trader}</div>'
                        f'<div class="bio-role">{bio.get("role","")}</div>'
                        f'<div class="bio-line"><strong>Track record:</strong> {bio.get("track_record","")}</div>'
                        f'<div class="bio-line"><strong>Style:</strong> {bio.get("style","")}</div>'
                        f'<div class="bio-line"><strong>Notable:</strong> {bio.get("notable","")}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        reasoning = SCORING_EXPLAINER.get(cat, '')
        if reasoning:
            st.markdown(
                f'<div class="ai-box">'
                f'<div class="ai-label">Why Mirror AI picked this</div>'
                f'<div class="ai-text">{reasoning}</div>'
                f'<div class="ai-summary">Confidence: <span style="color:{conf_color}">{conf_lbl}</span>'
                f'&nbsp;·&nbsp; Score: <span style="color:{accent}">{score:.2f}</span>'
                f'&nbsp;·&nbsp; {conviction}/{total} holders</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Action buttons
    decision_key = f"{cat}_{ticker}_{action}"
    col_a, col_b = st.columns([3, 2])
    with col_a:
        if is_sell:
            btn_lbl = f"MIRROR  SELL  {ticker}"
        else:
            btn_lbl = f"MIRROR  BUY  ${notional_now:,.0f}"
        if st.button(btn_lbl, key=f"{key_prefix}_approve", use_container_width=True, type="primary"):
            ok, result, notional = place_order(
                ticker,
                side=OrderSide.SELL if is_sell else OrderSide.BUY,
                category=cat, investors=investors,
            )
            st.session_state.decisions[decision_key] = 'mirrored'
            save_decisions(st.session_state.decisions)
            verb = 'Sold' if is_sell else 'Bought'
            if ok:
                st.session_state.toasts.append((True, f"{verb}: {ticker}  ·  {result}"))
            else:
                st.session_state.toasts.append((False, f"Order failed: {result}"))
            st.rerun()
    with col_b:
        if st.button("SKIP", key=f"{key_prefix}_reject", use_container_width=True):
            st.session_state.decisions[decision_key] = 'skipped'
            save_decisions(st.session_state.decisions)
            st.rerun()

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FEED TAB
# ─────────────────────────────────────────────
if st.session_state.tab == 'feed':
    all_sug = load_suggestions()
    cat     = st.session_state.category
    accent  = CATEGORIES[cat]['accent']
    signals = all_sug.get(cat, [])

    pending = [s for s in signals
               if st.session_state.decisions.get(f"{cat}_{s['ticker']}_{s.get('action','BUY')}", 'pending') == 'pending']
    decided = [s for s in signals
               if st.session_state.decisions.get(f"{cat}_{s['ticker']}_{s.get('action','BUY')}", 'pending') != 'pending']

    col_t, col_c = st.columns([4, 1])
    with col_t:
        st.markdown(f'<div class="section-label">{CATEGORIES[cat]["label"]}  ·  Signal Feed</div>', unsafe_allow_html=True)
    with col_c:
        st.markdown(f'<div style="text-align:right;font-family:var(--mono);font-size:0.78rem;color:{accent};padding-top:20px">{len(pending)} pending</div>', unsafe_allow_html=True)

    if not signals:
        st.markdown('<div class="empty">No signals yet<br>Run fetcher.py to pull latest data</div>', unsafe_allow_html=True)
    elif not pending:
        st.markdown('<div class="empty">All signals reviewed<br>Check back after next refresh</div>', unsafe_allow_html=True)

    for i, s in enumerate(pending):
        render_signal_card(s, cat, accent, f"p_{cat}_{i}", _notional_now)

    if decided:
        st.markdown(f'<div class="section-label">Reviewed  ·  {len(decided)}</div>', unsafe_allow_html=True)
        for s in decided:
            ticker = s.get('ticker', '')
            action = s.get('action', 'BUY')
            dec    = st.session_state.decisions.get(f"{cat}_{ticker}_{action}", '')
            badge  = f'<span class="badge-{"mirrored" if dec == "mirrored" else "skipped"}">{"MIRRORED" if dec == "mirrored" else "SKIPPED"}</span>'
            side_c = 'var(--red)' if action == 'SELL' else accent
            st.markdown(
                f'<div class="card card-done" style="padding:10px 18px">'
                f'<div style="display:flex;justify-content:space-between;align-items:center">'
                f'<div style="display:flex;align-items:center;gap:8px">'
                f'<span class="ticker" style="color:{side_c};font-size:0.95rem">{ticker}</span>'
                f'<span class="badge badge-{"sell" if action=="SELL" else "buy"}">{action}</span>'
                f'</div>{badge}</div></div>',
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────
# POSITIONS TAB
# ─────────────────────────────────────────────
elif st.session_state.tab == 'positions':
    positions  = load_positions()
    trade_log  = load_trade_log()
    log_by_sym = {e['ticker']: e for e in trade_log}
    CAT_ACCENT = {k: v['accent'] for k, v in CATEGORIES.items()}

    st.markdown('<div class="section-label">Open Positions</div>', unsafe_allow_html=True)

    if not positions:
        st.markdown('<div class="empty">No open positions<br>Mirror signals in the Feed to start</div>', unsafe_allow_html=True)
    else:
        total_pnl = sum(float(p.unrealized_pl) for p in positions)
        total_val = sum(float(p.market_value)  for p in positions)
        pnl_c = 'var(--green)' if total_pnl >= 0 else 'var(--red)'

        c1, c2 = st.columns(2)
        with c1:
            st.metric("Portfolio value", f"${total_val:,.2f}")
        with c2:
            st.metric("Unrealized P&L", f"${total_pnl:+,.2f}")

        st.markdown('<br>', unsafe_allow_html=True)
        for p in sorted(positions, key=lambda x: float(x.unrealized_pl), reverse=True):
            pnl  = float(p.unrealized_pl)
            pct  = float(p.unrealized_plpc) * 100
            mval = float(p.market_value)
            pnl_c = 'var(--green)' if pnl >= 0 else 'var(--red)'
            log  = log_by_sym.get(p.symbol, {})
            c    = log.get('category', '')
            inv  = log.get('investors', '')
            acc  = CAT_ACCENT.get(c, 'var(--sub)')
            cat_tag = (
                f'<span style="font-size:0.56rem;font-family:var(--mono);color:{acc};'
                f'background:{acc}14;border:1px solid {acc}28;border-radius:4px;'
                f'padding:1px 5px;margin-left:6px">{c.upper()}</span>'
            ) if c else ''
            lurl = logo_url(p.symbol)
            logo_bit = f'<img src="{lurl}" style="width:22px;height:22px;border-radius:5px;margin-right:8px;vertical-align:middle" onerror="this.style.display=\'none\'" alt="">' if lurl else ''
            st.markdown(
                f'<div class="pos-row">'
                f'<div><div class="pos-sym">{logo_bit}{p.symbol}{cat_tag}</div>'
                f'<div class="pos-meta">{float(p.qty):.4f} sh  ·  ${float(p.current_price):,.2f}  ·  {inv[:35] or "—"}</div></div>'
                f'<div style="text-align:right">'
                f'<div style="font-family:var(--mono);font-size:0.93rem;color:{pnl_c};font-weight:600">${pnl:+,.2f}</div>'
                f'<div style="font-family:var(--mono);font-size:0.68rem;color:{pnl_c}">{pct:+.2f}%</div>'
                f'<div style="font-size:0.6rem;color:var(--sub);margin-top:1px">${mval:,.2f} mkt</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button("Refresh positions", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─────────────────────────────────────────────
# LEADERBOARD TAB
# ─────────────────────────────────────────────
elif st.session_state.tab == 'leaderboard':
    all_sug   = load_suggestions()
    positions = load_positions()
    trade_log = load_trade_log()
    pnl_by_sym = {p.symbol: float(p.unrealized_pl) for p in positions}
    cat_pnl    = {}
    for entry in trade_log:
        c = entry.get('category', '')
        s = entry.get('ticker', '')
        if c and s in pnl_by_sym:
            cat_pnl[c] = cat_pnl.get(c, 0.0) + pnl_by_sym[s]

    st.markdown('<div class="section-label">Leaderboard  ·  Signal strength by source</div>', unsafe_allow_html=True)

    for cat_key, cat_info in CATEGORIES.items():
        accent  = cat_info['accent']
        signals = all_sug.get(cat_key, [])
        if not signals:
            continue

        pnl = cat_pnl.get(cat_key)
        pnl_str = ''
        if pnl is not None:
            col = 'var(--green)' if pnl >= 0 else 'var(--red)'
            pnl_str = f'  <span style="font-family:var(--mono);font-size:0.68rem;color:{col}">${pnl:+,.2f}</span>'

        holder_scores: dict = {}
        for sg in signals:
            for inv in sg.get('investors', '').split(','):
                inv = inv.strip()
                if inv:
                    holder_scores[inv] = holder_scores.get(inv, 0) + float(sg.get('score', 0))

        ranked    = sorted(holder_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = ranked[0][1] if ranked else 1

        st.markdown(
            f'<div class="section-label" style="border-color:{accent}20">'
            f'{cat_info["label"].upper()}{pnl_str}</div>',
            unsafe_allow_html=True,
        )

        for i, (name, score) in enumerate(ranked[:7]):
            bar_pct   = int((score / max_score) * 100)
            rank_cols = ['#fbbf24', '#94a3b8', '#b45309']
            rank_col  = rank_cols[i] if i < 3 else 'var(--sub)'
            st.markdown(
                f'<div class="lb-row" style="border-color:{accent}12">'
                f'<span class="lb-rank" style="color:{rank_col}">#{i+1:02d}</span>'
                f'<div style="flex:1"><div class="lb-name">{name}</div>'
                f'<div class="bar-track" style="margin:4px 0 0">'
                f'<div style="height:2px;border-radius:2px;background:{accent};width:{bar_pct}%;opacity:0.65"></div>'
                f'</div></div>'
                f'<span class="lb-score" style="color:{accent}">{score:.1f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button("Refresh all data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
