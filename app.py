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
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# DESIGN SYSTEM
# Inspired by Bloomberg Terminal meets modern fintech (Robinhood/Revolut)
# Deep navy base, electric accents, glass-morphism cards
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root {
  --navy:    #050914;
  --navy2:   #080f20;
  --surface: #0d1528;
  --glass:   rgba(255,255,255,0.03);
  --border:  rgba(255,255,255,0.07);
  --border2: rgba(255,255,255,0.12);
  --green:   #00d4aa;
  --green2:  #00ffcc;
  --red:     #ff4757;
  --amber:   #ffa502;
  --blue:    #2ed0ff;
  --purple:  #a855f7;
  --gold:    #f59e0b;
  --text:    #e8eaf6;
  --sub:     #8892b0;
  --muted:   #3d4f6e;
  --mono:    'Space Mono', monospace;
  --sans:    'Space Grotesk', sans-serif;
}

html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"] {
  background: var(--navy) !important;
  font-family: var(--sans) !important;
  color: var(--text) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: var(--navy2) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

/* Hide default streamlit chrome */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu, footer { display: none !important; }

/* Main content padding */
[data-testid="stMainBlockContainer"] {
  padding: 24px 32px 80px !important;
  max-width: 900px !important;
}

/* Metrics */
[data-testid="metric-container"] {
  background: var(--glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 14px 18px !important;
  backdrop-filter: blur(10px) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--mono) !important;
  font-size: 1.35rem !important;
  font-weight: 700 !important;
  color: var(--green) !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.6rem !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  color: var(--sub) !important;
  font-family: var(--sans) !important;
}

/* Buttons */
div.stButton > button {
  width: 100% !important;
  border-radius: 8px !important;
  font-family: var(--mono) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.06em !important;
  padding: 10px 12px !important;
  border: 1px solid var(--border2) !important;
  background: var(--glass) !important;
  color: var(--sub) !important;
  transition: all 0.2s ease !important;
  cursor: pointer !important;
}
div.stButton > button:hover {
  border-color: var(--green) !important;
  color: var(--green) !important;
  background: rgba(0,212,170,0.08) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 20px rgba(0,212,170,0.15) !important;
}
div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, rgba(0,212,170,0.15), rgba(46,208,255,0.1)) !important;
  border-color: var(--green) !important;
  color: var(--green) !important;
  box-shadow: 0 0 20px rgba(0,212,170,0.1) !important;
}

/* Expander */
[data-testid="stExpander"] {
  background: var(--glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  margin-top: -8px !important;
  margin-bottom: 12px !important;
}
[data-testid="stExpander"] summary {
  font-family: var(--mono) !important;
  font-size: 0.68rem !important;
  letter-spacing: 0.1em !important;
  color: var(--sub) !important;
}

/* Charts */
[data-testid="stArrowVegaLiteChart"] { border-radius: 8px !important; overflow: hidden !important; }

/* ─── CUSTOM COMPONENTS ─── */

.wordmark {
  font-family: var(--mono);
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.25em;
  background: linear-gradient(90deg, var(--green), var(--blue));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  padding: 24px 20px 4px;
  text-align: center;
}
.sub-tag {
  font-size: 0.58rem;
  color: var(--muted);
  text-align: center;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  margin-bottom: 24px;
  font-family: var(--sans);
}
.nav-section {
  font-size: 0.55rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--muted);
  padding: 16px 20px 6px;
  font-family: var(--mono);
}
.divider { height: 1px; background: var(--border); margin: 12px 0; }
.section-label {
  font-size: 0.6rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 20px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
  font-family: var(--mono);
}

/* Signal card */
.card {
  background: linear-gradient(135deg, var(--surface), rgba(13,21,40,0.8));
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px 20px;
  margin-bottom: 12px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}
.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border2), transparent);
}
.card:hover { border-color: var(--border2); transform: translateY(-1px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
.card-sell { border-color: rgba(255,71,87,0.25) !important; }
.card-sell::before { background: linear-gradient(90deg, transparent, rgba(255,71,87,0.3), transparent) !important; }

.card-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; }
.ticker-row { display:flex; align-items:center; gap:10px; }
.ticker { font-family:var(--mono); font-size:1.3rem; font-weight:700; letter-spacing:0.04em; }
.badge {
  font-family:var(--mono); font-size:0.58rem; letter-spacing:0.1em;
  padding:3px 8px; border-radius:4px;
}
.badge-buy  { background:rgba(0,212,170,0.12); border:1px solid rgba(0,212,170,0.3); color:var(--green); }
.badge-sell { background:rgba(255,71,87,0.12);  border:1px solid rgba(255,71,87,0.3);  color:var(--red); }
.badge-high   { background:rgba(0,212,170,0.12); border:1px solid rgba(0,212,170,0.25); color:var(--green); }
.badge-medium { background:rgba(255,165,2,0.12); border:1px solid rgba(255,165,2,0.25); color:var(--amber); }
.badge-low    { background:rgba(136,146,176,0.1);border:1px solid rgba(136,146,176,0.2);color:var(--sub); }

.score-ring {
  font-family:var(--mono); font-size:1rem; font-weight:700;
  width:52px; height:52px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  border:2px solid; flex-shrink:0;
}

.meta { font-size:0.7rem; color:var(--sub); margin-bottom:10px; }
.pills { display:flex; flex-wrap:wrap; gap:4px; margin-bottom:12px; }
.pill {
  font-size:0.6rem; letter-spacing:0.07em; text-transform:uppercase;
  color:var(--sub); background:rgba(255,255,255,0.04);
  border:1px solid var(--border); border-radius:4px;
  padding:2px 8px; font-family:var(--mono);
}
.bar-track { background:var(--border); border-radius:3px; height:3px; margin:8px 0 12px; }
.stats { display:flex; gap:20px; }
.stat-label { font-size:0.58rem; color:var(--muted); letter-spacing:0.1em; text-transform:uppercase; margin-bottom:3px; font-family:var(--sans); }
.stat-val   { font-family:var(--mono); font-size:0.85rem; color:var(--text); }

/* Decided cards */
.card-done { opacity:0.35; }
.badge-ok  { font-family:var(--mono); font-size:0.58rem; padding:2px 8px; border-radius:4px; background:rgba(0,212,170,0.1); border:1px solid var(--green); color:var(--green); }
.badge-no  { font-family:var(--mono); font-size:0.58rem; padding:2px 8px; border-radius:4px; background:rgba(255,71,87,0.1);  border:1px solid var(--red);   color:var(--red); }

/* Positions */
.pos-row {
  display:flex; justify-content:space-between; align-items:center;
  padding:14px 0; border-bottom:1px solid var(--border);
}
.pos-sym { font-family:var(--mono); font-size:1rem; font-weight:700; color:var(--text); }
.pos-meta { font-size:0.65rem; color:var(--sub); margin-top:3px; }
.pnl-pos { font-family:var(--mono); color:var(--green); }
.pnl-neg { font-family:var(--mono); color:var(--red); }

/* Leaderboard */
.lb-row {
  display:flex; align-items:center; gap:14px;
  background:var(--glass); border:1px solid var(--border);
  border-radius:12px; padding:12px 16px; margin-bottom:8px;
  transition:border-color 0.15s;
}
.lb-row:hover { border-color:var(--border2); }
.lb-rank { font-family:var(--mono); font-size:0.7rem; color:var(--muted); min-width:28px; }
.lb-name { font-size:0.85rem; font-weight:500; color:var(--text); flex:1; }
.lb-score { font-family:var(--mono); font-size:0.82rem; }

/* Toasts */
.toast-ok  { background:rgba(0,212,170,0.08); border:1px solid rgba(0,212,170,0.3); border-radius:10px; padding:10px 16px; font-size:0.75rem; color:var(--green); font-family:var(--mono); margin-bottom:8px; }
.toast-err { background:rgba(255,71,87,0.08);  border:1px solid rgba(255,71,87,0.3);  border-radius:10px; padding:10px 16px; font-size:0.75rem; color:var(--red);   font-family:var(--mono); margin-bottom:8px; }

/* Deep dive */
.dd-section { font-size:0.58rem; letter-spacing:0.18em; text-transform:uppercase; color:var(--muted); margin:14px 0 8px; font-family:var(--mono); }
.bio-card {
  background:rgba(255,255,255,0.02); border:1px solid var(--border);
  border-radius:10px; padding:14px 16px; margin-bottom:8px;
}
.bio-name  { font-size:0.88rem; font-weight:600; color:var(--text); margin-bottom:2px; }
.bio-role  { font-size:0.65rem; color:var(--sub); margin-bottom:8px; }
.bio-line  { font-size:0.72rem; color:var(--sub); line-height:1.6; margin-bottom:4px; }
.bio-line strong { color:var(--text); }
.ai-box {
  background:linear-gradient(135deg, rgba(0,212,170,0.04), rgba(46,208,255,0.03));
  border:1px solid rgba(0,212,170,0.15); border-radius:10px;
  padding:14px 16px; margin-top:10px;
}
.ai-label { font-size:0.58rem; letter-spacing:0.18em; text-transform:uppercase; color:var(--green); margin-bottom:8px; font-family:var(--mono); }
.ai-text  { font-size:0.73rem; color:var(--sub); line-height:1.7; }
.ai-summary { font-size:0.72rem; color:var(--text); margin-top:8px; font-family:var(--mono); }

/* Empty */
.empty { text-align:center; padding:60px 20px; color:var(--muted); font-size:0.78rem; font-family:var(--mono); letter-spacing:0.05em; line-height:2; }

/* Category accent dots in sidebar */
.cat-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; }

/* Settings section */
.setting-row { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid var(--border); }
.setting-label { font-size:0.75rem; color:var(--text); }
.setting-sub   { font-size:0.62rem; color:var(--sub); margin-top:2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
CATEGORIES = {
    'politicians': {'label': 'Politicians',    'accent': '#00d4aa', 'count': 8},
    'ceos':        {'label': 'Superinvestors', 'accent': '#2ed0ff', 'count': 7},
    'athletes':    {'label': 'Athletes',       'accent': '#ffa502', 'count': 7},
    'sectors':     {'label': 'Sectors',        'accent': '#a855f7', 'count': 7},
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

def get_trade_notional():
    """
    Scale with equity: 0.5% of current equity, minimum $10.
    This mirrors the proportional approach — as your account grows, so does each trade.
    """
    acct = load_account()
    if acct:
        equity = float(acct.equity)
        pct = st.session_state.get('trade_pct', 0.5) / 100.0
        return max(10.0, round(equity * pct, 2))
    return 50.0

def place_order(symbol, side=OrderSide.BUY, category='', investors=''):
    client = get_client()
    if not client:
        return False, "Alpaca credentials not configured", None
    notional = get_trade_notional()
    try:
        if side == OrderSide.SELL:
            # For sells: close the existing position
            positions = load_positions()
            pos = next((p for p in positions if p.symbol == symbol), None)
            if not pos:
                return False, f"No open position in {symbol} to sell", None
            req = MarketOrderRequest(
                symbol=symbol,
                qty=float(pos.qty),
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
        else:
            req = MarketOrderRequest(
                symbol=symbol, notional=notional,
                side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
            )
        order = client.submit_order(req)
        import time as _t; _t.sleep(1.5)
        try:
            o      = client.get_order_by_id(order.id)
            status = str(o.status).split('.')[-1].lower()
        except Exception:
            status = 'submitted'
        append_trade_log({
            'ticker':    symbol,
            'side':      'sell' if side == OrderSide.SELL else 'buy',
            'category':  category,
            'investors': investors,
            'notional':  notional,
            'order_id':  str(order.id),
            'status':    status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
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

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="wordmark">MIRROR AI</div>', unsafe_allow_html=True)

    sug   = load_suggestions()
    lu    = sug.get('last_updated')
    fresh = 'No data'
    if lu:
        age   = datetime.now(timezone.utc) - datetime.fromisoformat(lu)
        h     = int(age.total_seconds() // 3600)
        fresh = f"Updated {h}h ago" if h < 24 else f"Updated {age.days}d ago"
    st.markdown(f'<div class="sub-tag">{fresh}</div>', unsafe_allow_html=True)

    acct = load_account()
    if acct:
        eq   = float(acct.equity)
        bp   = float(acct.buying_power)
        pnl  = eq - float(acct.last_equity)
        pc   = 'pnl-pos' if pnl >= 0 else 'pnl-neg'
        st.markdown(f"""
        <div style="padding:0 16px 16px">
          <div style="background:var(--glass);border:1px solid var(--border);border-radius:12px;padding:14px">
            <div style="font-size:0.58rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;font-family:var(--mono)">Portfolio</div>
            <div style="font-family:var(--mono);font-size:1.4rem;font-weight:700;color:var(--green);margin-bottom:4px">${eq:,.0f}</div>
            <div style="display:flex;justify-content:space-between;font-size:0.68rem;margin-top:6px">
              <span style="color:var(--sub)">Buying power</span>
              <span style="font-family:var(--mono);color:var(--text)">${bp:,.0f}</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:0.68rem;margin-top:4px">
              <span style="color:var(--sub)">Today</span>
              <span style="font-family:var(--mono);color:{'var(--green)' if pnl>=0 else 'var(--red)'}">${pnl:+,.2f}</span>
            </div>
          </div>
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

    st.markdown('<div class="nav-section">Settings</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0 4px">
      <div class="setting-label">Trade size per signal</div>
      <div class="setting-sub">% of portfolio equity</div>
    </div>""", unsafe_allow_html=True)
    trade_pct = st.slider(
        "Trade %", min_value=0.1, max_value=5.0,
        value=float(st.session_state.trade_pct),
        step=0.1, format="%.1f%%",
        label_visibility="collapsed",
    )
    st.session_state.trade_pct = trade_pct
    notional_preview = get_trade_notional()
    st.markdown(f"""
    <div style="font-size:0.65rem;color:var(--sub);text-align:center;margin-top:4px;font-family:var(--mono)">
      ≈ ${notional_preview:,.2f} per trade
    </div>""", unsafe_allow_html=True)

    if st.button("Clear cache", key="clear_cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────
# TOASTS
# ─────────────────────────────────────────────
for ok, msg in st.session_state.toasts:
    st.markdown(f'<div class="{"toast-ok" if ok else "toast-err"}">{msg}</div>', unsafe_allow_html=True)
st.session_state.toasts = []


# ─────────────────────────────────────────────
# FEED TAB
# ─────────────────────────────────────────────
def render_signal_card(s, cat, accent, key_prefix):
    ticker     = s.get('ticker', '')
    score      = float(s.get('score', 0))
    conviction = int(s.get('conviction', 1))
    investors  = s.get('investors', '')
    buy_count  = int(s.get('buy_count', conviction))
    action     = s.get('action', 'BUY')
    is_sell    = action == 'SELL'
    total      = CATEGORIES[cat]['count']
    bar_pct    = min(100, int((conviction / total) * 100))
    conf_label_, conf_color = confidence_label(conviction, total, score)
    profile    = TICKER_PROFILES.get(ticker, {})
    data_as_of = s.get('data_as_of', '')
    side_cls   = 'card-sell' if is_sell else ''
    badge_cls  = 'badge-sell' if is_sell else 'badge-buy'
    ring_color = 'var(--red)' if is_sell else accent
    pills      = ''.join(f'<span class="pill">{p.strip()}</span>' for p in investors.split(',') if p.strip())
    conf_cls   = f'badge-{conf_label_.lower()}'

    st.markdown(f"""
    <div class="card {side_cls}">
      <div class="card-top">
        <div>
          <div class="ticker-row">
            <span class="ticker" style="color:{ring_color}">{ticker}</span>
            <span class="badge {badge_cls}">{action}</span>
            <span class="badge {conf_cls}">{conf_label_}</span>
          </div>
          {f'<div class="meta">{profile.get("company","")} &nbsp;·&nbsp; {profile.get("sector","")}</div>' if profile else '<div class="meta" style="height:18px"></div>'}
          {f'<div style="font-size:0.6rem;color:var(--muted);margin-top:-4px;margin-bottom:4px">Holdings as of {data_as_of}</div>' if data_as_of else ''}
        </div>
        <div class="score-ring" style="color:{ring_color};border-color:{ring_color}40;background:{ring_color}08">
          {score:.1f}
        </div>
      </div>
      <div class="pills">{pills}</div>
      <div class="bar-track"><div style="height:3px;border-radius:3px;background:{ring_color};width:{bar_pct}%;opacity:0.8"></div></div>
      <div class="stats">
        <div class="stat"><div class="stat-label">Conviction</div><div class="stat-val">{conviction}/{total}</div></div>
        <div class="stat"><div class="stat-label">Disclosures</div><div class="stat-val">{buy_count}</div></div>
        <div class="stat"><div class="stat-label">Signal</div><div class="stat-val">{score:.2f}</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Deep dive expander
    with st.expander(f"Deep dive  {ticker}", expanded=False):
        bars = fetch_price_history(ticker)
        if bars:
            closes  = [b[1] for b in bars]
            pct_chg = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] else 0
            chg_col = '#00d4aa' if pct_chg >= 0 else '#ff4757'
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
              <span style="font-family:var(--mono);font-size:1.1rem;font-weight:700;color:{accent}">${closes[-1]:,.2f}</span>
              <span style="font-family:var(--mono);font-size:0.78rem;color:{chg_col}">{pct_chg:+.1f}% · 30 days</span>
            </div>""", unsafe_allow_html=True)
            st.line_chart({'Price': closes}, height=100, use_container_width=True)
        else:
            st.markdown('<div style="font-size:0.7rem;color:var(--sub);padding:8px 0">Price history unavailable</div>', unsafe_allow_html=True)

        if profile:
            risk = profile.get('risk', 3)
            st.markdown(f"""
            <div class="dd-section">About {ticker}</div>
            <div style="font-size:0.75rem;color:var(--text);line-height:1.7;margin-bottom:6px">{profile.get('summary','')}</div>
            <div style="font-size:0.65rem;color:var(--sub)">Risk &nbsp;<span style="font-family:var(--mono);color:var(--text)">{'|' * risk}{'·' * (5 - risk)}</span> {risk}/5</div>
            """, unsafe_allow_html=True)

        trader_list = [p.strip() for p in investors.split(',') if p.strip()]
        if trader_list:
            st.markdown('<div class="dd-section">Who is behind this signal</div>', unsafe_allow_html=True)
            for trader in trader_list:
                bio = TRADER_BIOS.get(trader, {})
                if bio:
                    st.markdown(f"""
                    <div class="bio-card">
                      <div class="bio-name">{trader}</div>
                      <div class="bio-role">{bio.get('role','')}</div>
                      <div class="bio-line"><strong>Track record:</strong> {bio.get('track_record','')}</div>
                      <div class="bio-line"><strong>Style:</strong> {bio.get('style','')}</div>
                      <div class="bio-line"><strong>Notable:</strong> {bio.get('notable','')}</div>
                    </div>""", unsafe_allow_html=True)

        reasoning = SCORING_EXPLAINER.get(cat, '')
        if reasoning:
            st.markdown(f"""
            <div class="ai-box">
              <div class="ai-label">Why Mirror AI picked this</div>
              <div class="ai-text">{reasoning}</div>
              <div class="ai-summary">
                Confidence: <span style="color:{conf_color}">{conf_label_}</span>
                &nbsp;·&nbsp; Score: <span style="color:{accent}">{score:.2f}</span>
                &nbsp;·&nbsp; {conviction} of {total} holders
              </div>
            </div>""", unsafe_allow_html=True)

    # Action buttons
    col_a, col_b = st.columns([3, 2])
    decision_key = f"{cat}_{ticker}_{action}"
    with col_a:
        btn_label = f"MIRROR  {'SELL' if is_sell else 'BUY'}  ${notional_preview:,.0f}" if not is_sell else f"MIRROR  SELL  {ticker}"
        if st.button(btn_label, key=f"{key_prefix}_approve", use_container_width=True):
            ok, result, notional = place_order(
                ticker,
                side=OrderSide.SELL if is_sell else OrderSide.BUY,
                category=cat, investors=investors,
            )
            st.session_state.decisions[decision_key] = 'mirrored'
            save_decisions(st.session_state.decisions)
            if ok:
                st.session_state.toasts.append((True, f"{'Sold' if is_sell else 'Bought'}: {ticker}  ·  {result}"))
            else:
                st.session_state.toasts.append((False, f"Order failed: {result}"))
            st.rerun()
    with col_b:
        if st.button("SKIP", key=f"{key_prefix}_reject", use_container_width=True):
            st.session_state.decisions[decision_key] = 'skipped'
            save_decisions(st.session_state.decisions)
            st.rerun()


if st.session_state.tab == 'feed':
    all_sug = load_suggestions()
    cat     = st.session_state.category
    accent  = CATEGORIES[cat]['accent']
    signals = all_sug.get(cat, [])

    pending = [s for s in signals if st.session_state.decisions.get(
        f"{cat}_{s['ticker']}_{s.get('action','BUY')}", 'pending') == 'pending']
    decided = [s for s in signals if st.session_state.decisions.get(
        f"{cat}_{s['ticker']}_{s.get('action','BUY')}", 'pending') != 'pending']

    col_title, col_count = st.columns([4, 1])
    with col_title:
        st.markdown(f'<div class="section-label">{CATEGORIES[cat]["label"]} &nbsp;·&nbsp; Signal Feed</div>', unsafe_allow_html=True)
    with col_count:
        st.markdown(f'<div style="text-align:right;font-family:var(--mono);font-size:0.8rem;color:{accent};padding-top:20px">{len(pending)} pending</div>', unsafe_allow_html=True)

    if not signals:
        st.markdown('<div class="empty">No signals available<br>Run fetcher.py to pull latest data</div>', unsafe_allow_html=True)
    elif not pending:
        st.markdown('<div class="empty">All signals reviewed<br>Check back after next data refresh</div>', unsafe_allow_html=True)

    for i, s in enumerate(pending):
        render_signal_card(s, cat, accent, f"pending_{cat}_{i}")

    if decided:
        st.markdown(f'<div class="section-label">Reviewed &nbsp;·&nbsp; {len(decided)}</div>', unsafe_allow_html=True)
        for s in decided:
            ticker   = s.get('ticker', '')
            action   = s.get('action', 'BUY')
            dec      = st.session_state.decisions.get(f"{cat}_{ticker}_{action}", '')
            badge    = '<span class="badge-ok">MIRRORED</span>' if dec == 'mirrored' else '<span class="badge-no">SKIPPED</span>'
            side_col = 'var(--red)' if action == 'SELL' else accent
            st.markdown(f"""
            <div class="card card-done" style="padding:12px 18px">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div style="display:flex;align-items:center;gap:10px">
                  <span class="ticker" style="color:{side_col};font-size:1rem">{ticker}</span>
                  <span class="badge {'badge-sell' if action=='SELL' else 'badge-buy'}">{action}</span>
                </div>
                {badge}
              </div>
            </div>""", unsafe_allow_html=True)


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
        st.markdown('<div class="empty">No open positions<br>Mirror signals in the Feed to start building your portfolio</div>', unsafe_allow_html=True)
    else:
        total_pnl = sum(float(p.unrealized_pl) for p in positions)
        total_val = sum(float(p.market_value)  for p in positions)
        pnl_col   = 'var(--green)' if total_pnl >= 0 else 'var(--red)'
        st.markdown(f"""
        <div style="display:flex;gap:16px;margin-bottom:20px">
          <div style="flex:1;background:var(--glass);border:1px solid var(--border);border-radius:12px;padding:14px 18px">
            <div class="stat-label">Portfolio value</div>
            <div style="font-family:var(--mono);font-size:1.1rem;color:var(--text)">${total_val:,.2f}</div>
          </div>
          <div style="flex:1;background:var(--glass);border:1px solid var(--border);border-radius:12px;padding:14px 18px">
            <div class="stat-label">Unrealized P&L</div>
            <div style="font-family:var(--mono);font-size:1.1rem;color:{pnl_col}">${total_pnl:+,.2f}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        for p in sorted(positions, key=lambda x: float(x.unrealized_pl), reverse=True):
            pnl  = float(p.unrealized_pl)
            pct  = float(p.unrealized_plpc) * 100
            mval = float(p.market_value)
            pnl_col = 'var(--green)' if pnl >= 0 else 'var(--red)'
            log  = log_by_sym.get(p.symbol, {})
            cat  = log.get('category', '')
            inv  = log.get('investors', '')
            acc  = CAT_ACCENT.get(cat, 'var(--sub)')
            tag  = f'<span style="font-size:0.58rem;font-family:var(--mono);color:{acc};background:{acc}14;border:1px solid {acc}30;border-radius:4px;padding:1px 6px;margin-left:8px">{cat.upper()}</span>' if cat else ''
            st.markdown(f"""
            <div class="pos-row">
              <div>
                <div class="pos-sym">{p.symbol}{tag}</div>
                <div class="pos-meta">{float(p.qty):.4f} sh &nbsp;·&nbsp; ${float(p.current_price):,.2f} &nbsp;·&nbsp; {inv[:35] if inv else '—'}</div>
              </div>
              <div style="text-align:right">
                <div style="font-family:var(--mono);font-size:0.95rem;color:{pnl_col};font-weight:600">${pnl:+,.2f}</div>
                <div style="font-family:var(--mono);font-size:0.7rem;color:{pnl_col}">{pct:+.2f}%</div>
                <div style="font-size:0.62rem;color:var(--sub);margin-top:2px">${mval:,.2f} market</div>
              </div>
            </div>""", unsafe_allow_html=True)

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

    pnl_by_sym  = {p.symbol: float(p.unrealized_pl) for p in positions}
    cat_pnl     = {}
    for entry in trade_log:
        c = entry.get('category', '')
        s = entry.get('ticker', '')
        if c and s in pnl_by_sym:
            cat_pnl[c] = cat_pnl.get(c, 0.0) + pnl_by_sym[s]

    st.markdown('<div class="section-label">Leaderboard &nbsp;·&nbsp; Signal strength by source</div>', unsafe_allow_html=True)

    for cat_key, cat_info in CATEGORIES.items():
        accent  = cat_info['accent']
        signals = all_sug.get(cat_key, [])
        if not signals:
            continue

        pnl     = cat_pnl.get(cat_key)
        pnl_str = ''
        if pnl is not None:
            col = 'var(--green)' if pnl >= 0 else 'var(--red)'
            pnl_str = f'&nbsp;<span style="font-family:var(--mono);font-size:0.7rem;color:{col}">${pnl:+,.2f}</span>'

        holder_scores: dict = {}
        for s in signals:
            for inv in s.get('investors', '').split(','):
                inv = inv.strip()
                if inv:
                    holder_scores[inv] = holder_scores.get(inv, 0) + float(s.get('score', 0))

        ranked    = sorted(holder_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = ranked[0][1] if ranked else 1

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin:20px 0 10px">
          <div style="font-size:0.6rem;letter-spacing:0.18em;text-transform:uppercase;color:var(--muted);font-family:var(--mono);padding-bottom:8px;border-bottom:1px solid {accent}25;flex:1">
            {cat_info['label'].upper()}{pnl_str}
          </div>
        </div>""", unsafe_allow_html=True)

        for i, (name, score) in enumerate(ranked[:7]):
            bar_pct = int((score / max_score) * 100)
            rank_col = '#f59e0b' if i == 0 else ('#94a3b8' if i == 1 else ('#cd7f32' if i == 2 else 'var(--sub)'))
            st.markdown(f"""
            <div class="lb-row" style="border-color:{accent}15">
              <span class="lb-rank" style="color:{rank_col}">#{i+1:02d}</span>
              <div style="flex:1">
                <div class="lb-name">{name}</div>
                <div class="bar-track" style="margin:5px 0 0"><div style="height:3px;border-radius:3px;background:{accent};width:{bar_pct}%;opacity:0.7"></div></div>
              </div>
              <span class="lb-score" style="color:{accent}">{score:.1f}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button("Refresh all data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
