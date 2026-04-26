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

st.set_page_config(page_title="MIRROR AI", layout="wide", initial_sidebar_state="expanded")

# ── CSS ──────────────────────────────────────────────────────────────────────
# IMPORTANT: No curly-brace CSS values inside Python f-strings in st.markdown.
# All dynamic colors go through CSS custom properties set on data attributes,
# or through pre-defined accent classes (acc-green, acc-blue, etc.).
# ─────────────────────────────────────────────────────────────────────────────
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root {
  --bg:      #04080f;
  --surf:    #080e1c;
  --card:    #0b1222;
  --glass:   rgba(255,255,255,0.025);
  --bdr:     rgba(255,255,255,0.07);
  --bdr2:    rgba(255,255,255,0.12);
  --green:   #00d4aa;
  --red:     #ff4757;
  --amber:   #ffa502;
  --blue:    #38bdf8;
  --purple:  #a78bfa;
  --gold:    #fbbf24;
  --silver:  #94a3b8;
  --bronze:  #b45309;
  --text:    #e2e8f0;
  --sub:     #7c8fad;
  --muted:   #3a4a62;
  --mono:    'Space Mono', monospace;
  --sans:    'Space Grotesk', sans-serif;
}

html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: var(--sans) !important;
  color: var(--text) !important;
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu, footer { display: none !important; }

[data-testid="stMainBlockContainer"] {
  padding: 20px 28px 80px !important;
  max-width: 860px !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: var(--surf) !important;
  border-right: 1px solid var(--bdr) !important;
  min-width: 230px !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
section[data-testid="stSidebar"][aria-expanded="false"] { margin-left: -230px !important; }

/* Metrics */
[data-testid="metric-container"] {
  background: var(--glass) !important;
  border: 1px solid var(--bdr) !important;
  border-radius: 12px !important;
  padding: 14px 18px !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--mono) !important;
  font-size: 1.2rem !important;
  font-weight: 700 !important;
  color: var(--green) !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.58rem !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--sub) !important;
}

/* Buttons */
div.stButton > button {
  width: 100% !important;
  border-radius: 8px !important;
  font-family: var(--mono) !important;
  font-size: 0.68rem !important;
  letter-spacing: 0.07em !important;
  padding: 9px 12px !important;
  border: 1px solid var(--bdr2) !important;
  background: var(--glass) !important;
  color: var(--sub) !important;
  transition: all 0.18s ease !important;
}
div.stButton > button:hover {
  border-color: var(--green) !important;
  color: var(--green) !important;
  background: rgba(0,212,170,0.07) !important;
  transform: translateY(-1px) !important;
}
div.stButton > button[kind="primary"] {
  background: rgba(0,212,170,0.1) !important;
  border-color: var(--green) !important;
  color: var(--green) !important;
}

/* Expander */
[data-testid="stExpander"] {
  background: var(--glass) !important;
  border: 1px solid var(--bdr) !important;
  border-radius: 10px !important;
  margin-top: -4px !important;
  margin-bottom: 10px !important;
}
[data-testid="stExpander"] summary {
  font-family: var(--mono) !important;
  font-size: 0.65rem !important;
  letter-spacing: 0.09em !important;
  color: var(--sub) !important;
}

/* ── Accent color classes (no curly braces needed inline) ── */
.acc-green  { color: var(--green) !important; }
.acc-blue   { color: var(--blue)  !important; }
.acc-amber  { color: var(--amber) !important; }
.acc-purple { color: var(--purple)!important; }
.acc-red    { color: var(--red)   !important; }
.acc-sub    { color: var(--sub)   !important; }
.acc-muted  { color: var(--muted) !important; }
.acc-text   { color: var(--text)  !important; }
.acc-gold   { color: var(--gold)  !important; }
.acc-silver { color: var(--silver)!important; }
.acc-bronze { color: var(--bronze)!important; }

.bdr-green  { border-color: rgba(0,212,170,0.25)  !important; }
.bdr-blue   { border-color: rgba(56,189,248,0.25) !important; }
.bdr-amber  { border-color: rgba(255,165,2,0.25)  !important; }
.bdr-purple { border-color: rgba(167,139,250,0.25)!important; }
.bdr-red    { border-color: rgba(255,71,87,0.25)  !important; }

.bg-green  { background: rgba(0,212,170,0.08)  !important; }
.bg-blue   { background: rgba(56,189,248,0.08) !important; }
.bg-amber  { background: rgba(255,165,2,0.08)  !important; }
.bg-purple { background: rgba(167,139,250,0.08)!important; }
.bg-red    { background: rgba(255,71,87,0.08)  !important; }

.bar-green  { background: var(--green)  !important; }
.bar-blue   { background: var(--blue)   !important; }
.bar-amber  { background: var(--amber)  !important; }
.bar-purple { background: var(--purple) !important; }
.bar-red    { background: var(--red)    !important; }

/* ── Component styles ── */
.wordmark {
  font-family: var(--mono); font-size: 1rem; font-weight: 700;
  letter-spacing: 0.28em; padding: 22px 20px 2px; text-align: center;
  background: linear-gradient(90deg, var(--green), var(--blue));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.sub-tag {
  font-size: 0.55rem; color: var(--muted); text-align: center;
  letter-spacing: 0.17em; text-transform: uppercase; margin-bottom: 18px;
}
.nav-lbl {
  font-size: 0.52rem; letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--muted); padding: 14px 18px 5px; font-family: var(--mono);
}
.sec-lbl {
  font-size: 0.57rem; letter-spacing: 0.17em; text-transform: uppercase;
  color: var(--muted); margin: 18px 0 10px; padding-bottom: 8px;
  border-bottom: 1px solid var(--bdr); font-family: var(--mono);
}

/* Card */
.card {
  background: linear-gradient(160deg, var(--card) 0%, #05101e 100%);
  border: 1px solid var(--bdr);
  border-radius: 16px; padding: 16px 18px 12px;
  margin-bottom: 2px; position: relative; overflow: hidden;
  transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
}
.card:hover { border-color: var(--bdr2); transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0,0,0,0.35); }
.card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--bdr2), transparent);
}
.card-sell { border-color: rgba(255,71,87,0.18) !important; }

/* Card header */
.ch { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.ch-left { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
.logo-wrap {
  width: 40px; height: 40px; border-radius: 10px;
  background: var(--glass); border: 1px solid var(--bdr);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0; overflow: hidden;
}
.logo-wrap img { width: 28px; height: 28px; object-fit: contain; border-radius: 4px; }
.logo-fb { font-family: var(--mono); font-size: 0.7rem; color: var(--sub); font-weight: 700; }
.t-sym { font-family: var(--mono); font-size: 1.2rem; font-weight: 700; line-height: 1.1; }
.t-co  { font-size: 0.66rem; color: var(--sub); margin-top: 1px; }
.score-ring {
  font-family: var(--mono); font-size: 0.92rem; font-weight: 700;
  width: 46px; height: 46px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid; flex-shrink: 0;
}

/* Badges */
.badges { display: flex; gap: 5px; flex-wrap: wrap; margin: 8px 0 6px; }
.badge {
  font-family: var(--mono); font-size: 0.55rem; letter-spacing: 0.08em;
  padding: 2px 7px; border-radius: 4px; border: 1px solid;
}
.b-buy    { background: rgba(0,212,170,0.1);   border-color: rgba(0,212,170,0.3);  color: var(--green); }
.b-sell   { background: rgba(255,71,87,0.1);   border-color: rgba(255,71,87,0.3);  color: var(--red); }
.b-high   { background: rgba(0,212,170,0.08);  border-color: rgba(0,212,170,0.22); color: var(--green); }
.b-medium { background: rgba(255,165,2,0.08);  border-color: rgba(255,165,2,0.22); color: var(--amber); }
.b-low    { background: rgba(124,143,173,0.08);border-color: rgba(124,143,173,0.2);color: var(--sub); }

/* Pills */
.pills { display: flex; flex-wrap: wrap; gap: 4px; margin: 6px 0 8px; }
.pill {
  font-size: 0.58rem; color: var(--sub); background: rgba(255,255,255,0.03);
  border: 1px solid var(--bdr); border-radius: 4px; padding: 2px 7px; font-family: var(--mono);
}

/* Conviction bar track */
.btrack { background: var(--bdr); border-radius: 3px; height: 2px; margin: 6px 0 10px; position: relative; overflow: hidden; }

/* Stats */
.stats { display: flex; gap: 20px; margin-bottom: 4px; }
.sl { font-size: 0.55rem; color: var(--muted); letter-spacing: 0.09em; text-transform: uppercase; margin-bottom: 2px; }
.sv { font-family: var(--mono); font-size: 0.8rem; color: var(--text); }

/* Reviewed */
.card-done { opacity: 0.28; pointer-events: none; }
.b-mirrored { font-family: var(--mono); font-size: 0.55rem; padding: 2px 7px; border-radius: 4px; background: rgba(0,212,170,0.08); border: 1px solid var(--green); color: var(--green); }
.b-skipped  { font-family: var(--mono); font-size: 0.55rem; padding: 2px 7px; border-radius: 4px; background: rgba(255,71,87,0.08); border: 1px solid var(--red); color: var(--red); }

/* Toasts */
.t-ok  { background: rgba(0,212,170,0.07); border: 1px solid rgba(0,212,170,0.28); border-radius: 10px; padding: 9px 15px; font-size: 0.7rem; color: var(--green); font-family: var(--mono); margin-bottom: 7px; }
.t-err { background: rgba(255,71,87,0.07);  border: 1px solid rgba(255,71,87,0.28);  border-radius: 10px; padding: 9px 15px; font-size: 0.7rem; color: var(--red);   font-family: var(--mono); margin-bottom: 7px; }

/* Portfolio sidebar card */
.port-card { margin: 0 14px 16px; background: var(--glass); border: 1px solid var(--bdr); border-radius: 12px; padding: 14px 16px; }
.port-eq { font-family: var(--mono); font-size: 1.3rem; font-weight: 700; color: var(--green); margin-bottom: 6px; }
.port-row { display: flex; justify-content: space-between; font-size: 0.64rem; margin-top: 4px; }

/* Deep-dive */
.ddl { font-size: 0.54rem; letter-spacing: 0.17em; text-transform: uppercase; color: var(--muted); margin: 14px 0 7px; font-family: var(--mono); }
.bio-card { background: rgba(255,255,255,0.02); border: 1px solid var(--bdr); border-radius: 10px; padding: 12px 15px; margin-bottom: 7px; }
.bio-name { font-size: 0.84rem; font-weight: 600; color: var(--text); margin-bottom: 2px; }
.bio-role { font-size: 0.61rem; color: var(--sub); margin-bottom: 7px; }
.bio-line { font-size: 0.68rem; color: var(--sub); line-height: 1.65; margin-bottom: 3px; }
.bio-line strong { color: var(--text); }
.ai-box { background: rgba(0,212,170,0.03); border: 1px solid rgba(0,212,170,0.13); border-radius: 10px; padding: 13px 15px; margin-top: 10px; }
.ai-lbl  { font-size: 0.54rem; letter-spacing: 0.17em; text-transform: uppercase; color: var(--green); margin-bottom: 7px; font-family: var(--mono); }
.ai-text { font-size: 0.7rem; color: var(--sub); line-height: 1.72; }

/* Positions */
.pos-row { display: flex; justify-content: space-between; align-items: center; padding: 13px 0; border-bottom: 1px solid var(--bdr); }
.pos-sym { font-family: var(--mono); font-size: 0.96rem; font-weight: 700; }
.pos-meta { font-size: 0.61rem; color: var(--sub); margin-top: 3px; }

/* Leaderboard */
.lb-row { display: flex; align-items: center; gap: 12px; background: var(--glass); border: 1px solid var(--bdr); border-radius: 12px; padding: 10px 14px; margin-bottom: 7px; transition: border-color 0.15s; }
.lb-row:hover { border-color: var(--bdr2); }
.lb-rank { font-family: var(--mono); font-size: 0.67rem; color: var(--muted); min-width: 26px; }
.lb-name { font-size: 0.81rem; font-weight: 500; color: var(--text); flex: 1; }
.lb-score { font-family: var(--mono); font-size: 0.79rem; }

.empty { text-align: center; padding: 56px 20px; color: var(--muted); font-size: 0.75rem; font-family: var(--mono); letter-spacing: 0.05em; line-height: 2.2; }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
CATEGORIES = {
    'politicians': {'label': 'Politicians',    'acc': 'green',  'count': 8},
    'ceos':        {'label': 'Superinvestors', 'acc': 'blue',   'count': 7},
    'athletes':    {'label': 'Athletes',       'acc': 'amber',  'count': 7},
    'sectors':     {'label': 'Sectors',        'acc': 'purple', 'count': 7},
}
# Map acc name -> actual hex (for st.line_chart colors etc.)
ACC_HEX = {'green': '#00d4aa', 'blue': '#38bdf8', 'amber': '#ffa502', 'purple': '#a78bfa', 'red': '#ff4757'}

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
            'https://data.alpaca.markets/v2/stocks/' + symbol + '/bars',
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
    return ('https://logo.clearbit.com/' + domain) if domain else ''


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

def get_trade_notional(pct=None):
    if pct is None:
        pct = st.session_state.get('trade_pct', 0.5)
    acct = load_account()
    equity = float(acct.equity) if acct else 100000.0
    return max(10.0, round(equity * pct / 100.0, 2))

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
                return False, "No open position in " + symbol, None
            req = MarketOrderRequest(symbol=symbol, qty=float(pos.qty),
                                     side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
        else:
            req = MarketOrderRequest(symbol=symbol, notional=notional,
                                     side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
        order = client.submit_order(req)
        import time as _t; _t.sleep(1.5)
        try:
            o = client.get_order_by_id(order.id)
            status = str(o.status).split('.')[-1].lower()
        except Exception:
            status = 'submitted'
        append_trade_log({
            'ticker': symbol, 'side': 'sell' if side == OrderSide.SELL else 'buy',
            'category': category, 'investors': investors, 'notional': notional,
            'order_id': str(order.id), 'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
        return True, "id " + str(order.id)[:8] + "  " + status, notional
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

# Compute once at top of render
_notional = get_trade_notional()


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
            age = datetime.now(timezone.utc) - datetime.fromisoformat(lu)
            h   = int(age.total_seconds() // 3600)
            fresh = (str(h) + 'h ago') if h < 24 else (str(age.days) + 'd ago')
        except Exception:
            pass
    st.markdown('<div class="sub-tag">Updated ' + fresh + '</div>', unsafe_allow_html=True)

    acct = load_account()
    if acct:
        eq  = float(acct.equity)
        bp  = float(acct.buying_power)
        pnl = eq - float(acct.last_equity)
        pnl_cls = 'acc-green' if pnl >= 0 else 'acc-red'
        st.markdown(
            '<div class="port-card">'
            '<div style="font-size:0.54rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;font-family:var(--mono)">Portfolio</div>'
            '<div class="port-eq">$' + '{:,.0f}'.format(eq) + '</div>'
            '<div class="port-row"><span style="color:var(--sub)">Buying power</span>'
            '<span style="font-family:var(--mono);color:var(--text)">$' + '{:,.0f}'.format(bp) + '</span></div>'
            '<div class="port-row"><span style="color:var(--sub)">Today</span>'
            '<span class="' + pnl_cls + '" style="font-family:var(--mono)">$' + '{:+,.2f}'.format(pnl) + '</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="nav-lbl">Navigate</div>', unsafe_allow_html=True)
    for tk, tl in [('feed', 'Signal Feed'), ('positions', 'Positions'), ('leaderboard', 'Leaderboard')]:
        active = st.session_state.tab == tk
        if st.button(tl, key='nav_' + tk, use_container_width=True,
                     type='primary' if active else 'secondary'):
            st.session_state.tab = tk
            st.rerun()

    if st.session_state.tab == 'feed':
        st.markdown('<div class="nav-lbl">Category</div>', unsafe_allow_html=True)
        for ck, ci in CATEGORIES.items():
            active = st.session_state.category == ck
            if st.button(ci['label'], key='cat_' + ck, use_container_width=True,
                         type='primary' if active else 'secondary'):
                st.session_state.category = ck
                st.rerun()

    st.markdown('<div class="nav-lbl">Trade size</div>', unsafe_allow_html=True)
    trade_pct = st.slider('pct', min_value=0.1, max_value=5.0,
                          value=float(st.session_state.trade_pct),
                          step=0.1, format='%.1f%%', label_visibility='collapsed')
    st.session_state.trade_pct = trade_pct
    _notional = get_trade_notional(trade_pct)
    st.markdown(
        '<div style="font-size:0.61rem;color:var(--sub);text-align:center;margin-top:3px;font-family:var(--mono)">'
        + chr(8776) + ' $' + '{:,.2f}'.format(_notional) + ' per trade</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button('Refresh data', key='refresh', use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─────────────────────────────────────────────
# TOASTS
# ─────────────────────────────────────────────
for ok, msg in st.session_state.toasts:
    st.markdown('<div class="' + ('t-ok' if ok else 't-err') + '">' + msg + '</div>', unsafe_allow_html=True)
st.session_state.toasts = []


# ─────────────────────────────────────────────
# SIGNAL CARD
# ─────────────────────────────────────────────
def render_signal_card(s, cat, acc, key_prefix, notional):
    ticker     = s.get('ticker', '')
    score      = float(s.get('score', 0))
    conviction = int(s.get('conviction', 1))
    investors  = s.get('investors', '')
    buy_count  = int(s.get('buy_count', conviction))
    action     = s.get('action', 'BUY')
    is_sell    = action == 'SELL'
    total      = CATEGORIES[cat]['count']
    bar_pct    = min(100, int((conviction / total) * 100))
    conf_lbl, _ = confidence_label(conviction, total, score)
    profile    = TICKER_PROFILES.get(ticker, {})
    data_as_of = s.get('data_as_of', '')

    # Use acc-* classes — no curly-brace CSS values in the HTML string
    ticker_acc = 'acc-red' if is_sell else ('acc-' + acc)
    ring_acc   = 'acc-red bdr-red bg-red' if is_sell else ('acc-' + acc + ' bdr-' + acc + ' bg-' + acc)
    action_cls = 'b-sell' if is_sell else 'b-buy'
    conf_cls   = 'b-' + conf_lbl.lower()
    bar_cls    = 'bar-red' if is_sell else ('bar-' + acc)

    # Logo
    lurl = logo_url(ticker)
    if lurl:
        logo_html = (
            '<div class="logo-wrap">'
            '<img src="' + lurl + '" alt="" '
            'onerror="this.parentNode.innerHTML=\'<span class=\\\"logo-fb\\\">' + ticker[:2] + '</span>\'">'
            '</div>'
        )
    else:
        logo_html = '<div class="logo-wrap"><span class="logo-fb">' + ticker[:2] + '</span></div>'

    company = profile.get('company', '') or ''
    sector  = profile.get('sector', '') or ''
    co_line = company + ('  &middot;  ' + sector if sector else '')

    inv_list   = [p.strip() for p in investors.split(',') if p.strip()]
    pills_html = ''.join('<span class="pill">' + p + '</span>' for p in inv_list)

    date_line = (
        '<div style="font-size:0.57rem;margin-top:2px;color:var(--muted)">as of ' + data_as_of + '</div>'
        if data_as_of else ''
    )

    score_str = '{:.1f}'.format(score)
    bar_w     = str(bar_pct) + '%'

    st.markdown(
        '<div class="card' + (' card-sell' if is_sell else '') + '">'

        # Header row
        '<div class="ch">'
          '<div class="ch-left">'
            + logo_html +
            '<div>'
              '<div class="t-sym ' + ticker_acc + '">' + ticker + '</div>'
              '<div class="t-co">' + co_line + '</div>'
              + date_line +
            '</div>'
          '</div>'
          '<div class="score-ring ' + ring_acc + '">' + score_str + '</div>'
        '</div>'

        # Badges
        '<div class="badges">'
          '<span class="badge ' + action_cls + '">' + action + '</span>'
          '<span class="badge ' + conf_cls + '">' + conf_lbl + '</span>'
        '</div>'

        # Investor pills
        '<div class="pills">' + pills_html + '</div>'

        # Conviction bar
        '<div class="btrack"><div style="position:absolute;top:0;left:0;height:2px;border-radius:3px;opacity:0.75;width:' + bar_w + '" class="' + bar_cls + '"></div></div>'

        # Stats
        '<div class="stats">'
          '<div><div class="sl">Conviction</div><div class="sv">' + str(conviction) + '/' + str(total) + '</div></div>'
          '<div><div class="sl">Disclosures</div><div class="sv">' + str(buy_count) + '</div></div>'
          '<div><div class="sl">Score</div><div class="sv ' + ticker_acc + '">' + '{:.2f}'.format(score) + '</div></div>'
        '</div>'

        '</div>',
        unsafe_allow_html=True,
    )

    # Deep dive
    with st.expander('Deep dive  ' + ticker, expanded=False):
        bars = fetch_price_history(ticker)
        if bars:
            closes  = [b[1] for b in bars]
            pct_chg = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] else 0
            chg_cls = 'acc-green' if pct_chg >= 0 else 'acc-red'
            st.markdown(
                '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">'
                '<span class="' + ('acc-' + acc) + '" style="font-family:var(--mono);font-size:1rem;font-weight:700">$' + '{:,.2f}'.format(closes[-1]) + '</span>'
                '<span class="' + chg_cls + '" style="font-family:var(--mono);font-size:0.73rem">' + '{:+.1f}'.format(pct_chg) + '%  30d</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.line_chart({'Price': closes}, height=90, use_container_width=True)
        else:
            st.markdown('<div style="font-size:0.67rem;color:var(--sub);padding:6px 0">Price history unavailable</div>', unsafe_allow_html=True)

        if profile:
            risk = profile.get('risk', 3)
            bars_str = chr(9608) * risk + chr(9617) * (5 - risk)
            st.markdown(
                '<div class="ddl">About ' + ticker + '</div>'
                '<div style="font-size:0.71rem;color:var(--text);line-height:1.72;margin-bottom:6px">' + profile.get('summary', '') + '</div>'
                '<div style="font-size:0.61rem;color:var(--sub)">Risk &nbsp;'
                '<span style="font-family:var(--mono);color:var(--text)">' + bars_str + '</span>'
                '&nbsp;' + str(risk) + '/5</div>',
                unsafe_allow_html=True,
            )

        if inv_list:
            st.markdown('<div class="ddl">Who is behind this signal</div>', unsafe_allow_html=True)
            for trader in inv_list:
                bio = TRADER_BIOS.get(trader, {})
                if bio:
                    st.markdown(
                        '<div class="bio-card">'
                        '<div class="bio-name">' + trader + '</div>'
                        '<div class="bio-role">' + bio.get('role', '') + '</div>'
                        '<div class="bio-line"><strong>Track record:</strong> ' + bio.get('track_record', '') + '</div>'
                        '<div class="bio-line"><strong>Style:</strong> ' + bio.get('style', '') + '</div>'
                        '<div class="bio-line"><strong>Notable:</strong> ' + bio.get('notable', '') + '</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )

        reasoning = SCORING_EXPLAINER.get(cat, '')
        if reasoning:
            st.markdown(
                '<div class="ai-box">'
                '<div class="ai-lbl">Why Mirror AI picked this</div>'
                '<div class="ai-text">' + reasoning + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    # Buttons
    decision_key = cat + '_' + ticker + '_' + action
    col_a, col_b = st.columns([3, 2])
    with col_a:
        btn_lbl = ('MIRROR  SELL  ' + ticker) if is_sell else ('MIRROR  BUY  $' + '{:,.0f}'.format(notional))
        if st.button(btn_lbl, key=key_prefix + '_a', use_container_width=True, type='primary'):
            ok, result, amt = place_order(ticker,
                                          side=OrderSide.SELL if is_sell else OrderSide.BUY,
                                          category=cat, investors=investors)
            st.session_state.decisions[decision_key] = 'mirrored'
            save_decisions(st.session_state.decisions)
            verb = 'Sold' if is_sell else 'Bought'
            if ok:
                st.session_state.toasts.append((True, verb + ': ' + ticker + '  ' + result))
            else:
                st.session_state.toasts.append((False, 'Order failed: ' + result))
            st.rerun()
    with col_b:
        if st.button('SKIP', key=key_prefix + '_b', use_container_width=True):
            st.session_state.decisions[decision_key] = 'skipped'
            save_decisions(st.session_state.decisions)
            st.rerun()

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FEED
# ─────────────────────────────────────────────
if st.session_state.tab == 'feed':
    all_sug = load_suggestions()
    cat     = st.session_state.category
    acc     = CATEGORIES[cat]['acc']
    signals = all_sug.get(cat, [])

    pending = [s for s in signals
               if st.session_state.decisions.get(cat + '_' + s['ticker'] + '_' + s.get('action', 'BUY'), 'pending') == 'pending']
    decided = [s for s in signals
               if st.session_state.decisions.get(cat + '_' + s['ticker'] + '_' + s.get('action', 'BUY'), 'pending') != 'pending']

    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown('<div class="sec-lbl">' + CATEGORIES[cat]['label'] + '  &middot;  Signal Feed</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="acc-' + acc + '" style="text-align:right;font-family:var(--mono);font-size:0.76rem;padding-top:20px">' + str(len(pending)) + ' pending</div>', unsafe_allow_html=True)

    if not signals:
        st.markdown('<div class="empty">No signals yet<br>Run fetcher.py to pull latest data</div>', unsafe_allow_html=True)
    elif not pending:
        st.markdown('<div class="empty">All signals reviewed<br>Check back after next refresh</div>', unsafe_allow_html=True)

    for i, s in enumerate(pending):
        render_signal_card(s, cat, acc, 'p_' + cat + '_' + str(i), _notional)

    if decided:
        st.markdown('<div class="sec-lbl">Reviewed  &middot;  ' + str(len(decided)) + '</div>', unsafe_allow_html=True)
        for s in decided:
            ticker = s.get('ticker', '')
            action = s.get('action', 'BUY')
            dec    = st.session_state.decisions.get(cat + '_' + ticker + '_' + action, '')
            badge  = '<span class="b-mirrored">MIRRORED</span>' if dec == 'mirrored' else '<span class="b-skipped">SKIPPED</span>'
            acc_c  = 'acc-red' if action == 'SELL' else 'acc-' + acc
            a_cls  = 'b-sell' if action == 'SELL' else 'b-buy'
            st.markdown(
                '<div class="card card-done" style="padding:10px 18px">'
                '<div style="display:flex;justify-content:space-between;align-items:center">'
                '<div style="display:flex;align-items:center;gap:8px">'
                '<span class="t-sym ' + acc_c + '" style="font-size:0.93rem">' + ticker + '</span>'
                '<span class="badge ' + a_cls + '">' + action + '</span>'
                '</div>' + badge + '</div></div>',
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────
# POSITIONS
# ─────────────────────────────────────────────
elif st.session_state.tab == 'positions':
    positions  = load_positions()
    trade_log  = load_trade_log()
    log_by_sym = {e['ticker']: e for e in trade_log}

    st.markdown('<div class="sec-lbl">Open Positions</div>', unsafe_allow_html=True)

    if not positions:
        st.markdown('<div class="empty">No open positions<br>Mirror signals in the Feed to start</div>', unsafe_allow_html=True)
    else:
        total_pnl = sum(float(p.unrealized_pl) for p in positions)
        total_val = sum(float(p.market_value)  for p in positions)
        c1, c2 = st.columns(2)
        with c1:
            st.metric('Portfolio value', '$' + '{:,.2f}'.format(total_val))
        with c2:
            st.metric('Unrealized P&L', '$' + '{:+,.2f}'.format(total_pnl))

        st.markdown('<br>', unsafe_allow_html=True)
        for p in sorted(positions, key=lambda x: float(x.unrealized_pl), reverse=True):
            pnl  = float(p.unrealized_pl)
            pct  = float(p.unrealized_plpc) * 100
            mval = float(p.market_value)
            pnl_cls = 'acc-green' if pnl >= 0 else 'acc-red'
            log = log_by_sym.get(p.symbol, {})
            c   = log.get('category', '')
            inv = log.get('investors', '')
            cat_acc = CATEGORIES.get(c, {}).get('acc', '')
            cat_tag = (
                '<span class="acc-' + cat_acc + '" style="font-size:0.55rem;font-family:var(--mono);'
                'background:rgba(255,255,255,0.04);border:1px solid var(--bdr);border-radius:4px;'
                'padding:1px 5px;margin-left:6px">' + c.upper() + '</span>'
            ) if c and cat_acc else ''
            lurl = logo_url(p.symbol)
            logo_bit = '<img src="' + lurl + '" style="width:20px;height:20px;border-radius:5px;margin-right:7px;vertical-align:middle" onerror="this.style.display=\'none\'" alt="">' if lurl else ''

            st.markdown(
                '<div class="pos-row">'
                '<div><div class="pos-sym">' + logo_bit + p.symbol + cat_tag + '</div>'
                '<div class="pos-meta">' + '{:.4f}'.format(float(p.qty)) + ' sh  &middot;  $' + '{:,.2f}'.format(float(p.current_price)) + '  &middot;  ' + (inv[:35] or '—') + '</div></div>'
                '<div style="text-align:right">'
                '<div class="' + pnl_cls + '" style="font-family:var(--mono);font-size:0.9rem;font-weight:600">$' + '{:+,.2f}'.format(pnl) + '</div>'
                '<div class="' + pnl_cls + '" style="font-family:var(--mono);font-size:0.66rem">' + '{:+.2f}'.format(pct) + '%</div>'
                '<div style="font-size:0.59rem;color:var(--sub);margin-top:1px">$' + '{:,.2f}'.format(mval) + ' mkt</div>'
                '</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button('Refresh positions', use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─────────────────────────────────────────────
# LEADERBOARD
# ─────────────────────────────────────────────
elif st.session_state.tab == 'leaderboard':
    all_sug    = load_suggestions()
    positions  = load_positions()
    trade_log  = load_trade_log()
    pnl_by_sym = {p.symbol: float(p.unrealized_pl) for p in positions}
    cat_pnl    = {}
    for entry in trade_log:
        c = entry.get('category', '')
        sym = entry.get('ticker', '')
        if c and sym in pnl_by_sym:
            cat_pnl[c] = cat_pnl.get(c, 0.0) + pnl_by_sym[sym]

    st.markdown('<div class="sec-lbl">Leaderboard  &middot;  Signal strength by source</div>', unsafe_allow_html=True)

    for cat_key, cat_info in CATEGORIES.items():
        acc     = cat_info['acc']
        signals = all_sug.get(cat_key, [])
        if not signals:
            continue

        pnl     = cat_pnl.get(cat_key)
        pnl_str = ''
        if pnl is not None:
            pnl_cls = 'acc-green' if pnl >= 0 else 'acc-red'
            pnl_str = '  <span class="' + pnl_cls + '" style="font-family:var(--mono);font-size:0.66rem">$' + '{:+,.2f}'.format(pnl) + '</span>'

        holder_scores: dict = {}
        for sg in signals:
            for inv in sg.get('investors', '').split(','):
                inv = inv.strip()
                if inv:
                    holder_scores[inv] = holder_scores.get(inv, 0.0) + float(sg.get('score', 0))

        ranked    = sorted(holder_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = ranked[0][1] if ranked else 1.0

        st.markdown('<div class="sec-lbl">' + cat_info['label'].upper() + pnl_str + '</div>', unsafe_allow_html=True)

        rank_classes = ['acc-gold', 'acc-silver', 'acc-bronze']
        for i, (name, score) in enumerate(ranked[:7]):
            bar_pct   = int((score / max_score) * 100)
            rank_cls  = rank_classes[i] if i < 3 else 'acc-muted'
            st.markdown(
                '<div class="lb-row">'
                '<span class="lb-rank ' + rank_cls + '">#' + '{:02d}'.format(i+1) + '</span>'
                '<div style="flex:1"><div class="lb-name">' + name + '</div>'
                '<div class="btrack" style="margin:4px 0 0"><div class="' + 'bar-' + acc + '" style="position:absolute;top:0;left:0;height:2px;border-radius:2px;opacity:0.65;width:' + str(bar_pct) + '%"></div></div>'
                '</div>'
                '<span class="lb-score acc-' + acc + '">' + '{:.1f}'.format(score) + '</span>'
                '</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button('Refresh all data', use_container_width=True):
        st.cache_data.clear()
        st.rerun()
