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

# ─────────────────────────────────────────────────────────────────────────────
# CSS  — fixed topbar + CSS-only slide drawer (checkbox hack, iframe-safe)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root {
  --bg:     #04080f;
  --surf:   #07101f;
  --card:   #0a1220;
  --glass:  rgba(255,255,255,0.03);
  --bdr:    rgba(255,255,255,0.07);
  --bdr2:   rgba(255,255,255,0.13);
  --green:  #00d4aa;
  --red:    #ff4757;
  --amber:  #ffa502;
  --blue:   #38bdf8;
  --purple: #a78bfa;
  --gold:   #fbbf24;
  --silver: #94a3b8;
  --bronze: #b45309;
  --text:   #e2e8f0;
  --sub:    #7c8fad;
  --muted:  #3a4a62;
  --mono:   'Space Mono', monospace;
  --sans:   'Space Grotesk', sans-serif;
}

html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: var(--sans) !important;
  color: var(--text) !important;
}

/* Hide all Streamlit chrome and native sidebar */
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
#MainMenu,footer { display:none !important; }

[data-testid="stSidebar"] {
  background:#07101f !important;
  border-right:1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] > div:first-child { padding:0 8px !important; }
[data-testid="stSidebarCollapseButton"] button {
  background:rgba(0,212,170,0.07) !important;
  border:1px solid rgba(0,212,170,0.2) !important;
  color:#00d4aa !important;
}

/* Main content */
[data-testid="stMainBlockContainer"] {
  padding: 8px 28px 80px !important;
  max-width: 900px !important;
}
/* Collapse the topbar component iframe height to exactly 56px — no more */
[data-testid="stCustomComponentV1"] {
  height: 56px !important;
  min-height: 56px !important;
  max-height: 56px !important;
  overflow: hidden !important;
  border: none !important;
  margin-bottom: 8px !important;
}
[data-testid="stCustomComponentV1"] iframe {
  height: 56px !important;
  border: none !important;
}

/* ── TOPBAR ── */
#mir-topbar {
  position: fixed; top:0; left:0; right:0; height: var(--th);
  background: rgba(4,8,15,0.96);
  border-bottom: 1px solid var(--bdr);
  backdrop-filter: blur(18px);
  display: flex; align-items: center;
  padding: 0 18px; gap: 12px;
  z-index: 9100;
  font-family: var(--sans);
}

/* ── CHECKBOX toggle (the actual mechanism) ── */
#drw-toggle { display: none; }

/* Hamburger label */
#drw-btn {
  width:40px; height:40px; border-radius:8px; flex-shrink:0;
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:5px;
  cursor:pointer;
  border:1px solid transparent;
  transition: border-color 0.18s, background 0.18s;
}
#drw-btn:hover { border-color:var(--green); background:rgba(0,212,170,0.07); }
#drw-btn span {
  display:block; width:18px; height:1.5px; background:var(--sub);
  border-radius:2px; transition: transform 0.25s, opacity 0.2s, background 0.18s;
}
/* Animate to X when checked */
#drw-toggle:checked ~ #mir-topbar #drw-btn span:nth-child(1) {
  transform: translateY(6.5px) rotate(45deg); background:var(--green);
}
#drw-toggle:checked ~ #mir-topbar #drw-btn span:nth-child(2) {
  opacity:0;
}
#drw-toggle:checked ~ #mir-topbar #drw-btn span:nth-child(3) {
  transform: translateY(-6.5px) rotate(-45deg); background:var(--green);
}

/* Wordmark */
#mir-logo {
  font-family:var(--mono); font-size:0.98rem; font-weight:700; letter-spacing:0.22em;
  background:linear-gradient(90deg,var(--green),var(--blue));
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  margin-right:auto;
}

/* Portfolio chip */
#port-chip {
  font-family:var(--mono); font-size:0.61rem; letter-spacing:0.05em;
  padding:5px 12px; border-radius:6px;
  background:rgba(0,212,170,0.07); border:1px solid rgba(0,212,170,0.22); color:var(--green);
  white-space:nowrap; flex-shrink:0;
}

/* ── DRAWER ── */
#mir-drawer {
  position:fixed; top:var(--th); left:0; bottom:0; width:var(--dw);
  background:var(--surf); border-right:1px solid var(--bdr);
  transform: translateX(calc(-1 * var(--dw)));
  transition: transform 0.28s cubic-bezier(0.4,0,0.2,1);
  z-index:9099; overflow-y:auto; padding:20px 0 40px;
}
#drw-toggle:checked ~ #mir-drawer { transform: translateX(0); }

/* Overlay behind drawer */
#drw-overlay {
  position:fixed; inset:0;
  background:rgba(0,0,0,0);
  pointer-events:none;
  z-index:9098;
  transition: background 0.28s;
}
#drw-toggle:checked ~ #drw-overlay {
  background:rgba(0,0,0,0.55);
  pointer-events:auto;
  backdrop-filter:blur(2px);
}
/* clicking overlay closes drawer via label */
#drw-overlay { cursor:pointer; }

/* Drawer internals */
.drw-sec { font-family:var(--mono); font-size:0.51rem; letter-spacing:0.2em; text-transform:uppercase; color:var(--muted); padding:14px 20px 5px; }
.drw-div { height:1px; background:var(--bdr); margin:10px 18px; }
.drw-port { margin:0 14px 14px; background:var(--glass); border:1px solid var(--bdr); border-radius:12px; padding:14px 15px; }
.drw-eq { font-family:var(--mono); font-size:1.22rem; font-weight:700; color:var(--green); margin:5px 0; }
.drw-row { display:flex; justify-content:space-between; font-size:0.62rem; margin-top:4px; color:var(--sub); }
.drw-val { font-family:var(--mono); color:var(--text); }
.drw-port-lbl { font-size:0.51rem; letter-spacing:0.15em; text-transform:uppercase; color:var(--muted); font-family:var(--mono); }
.port-pnl { opacity:0.75; font-size:0.55rem; }
.drw-hint { font-size:0.62rem; color:var(--muted); padding:8px 20px 4px; font-family:var(--mono); }

/* ── Accent classes ── */
.acc-green  { color:var(--green)  !important; }
.acc-blue   { color:var(--blue)   !important; }
.acc-amber  { color:var(--amber)  !important; }
.acc-purple { color:var(--purple) !important; }
.acc-red    { color:var(--red)    !important; }
.acc-sub    { color:var(--sub)    !important; }
.acc-muted  { color:var(--muted)  !important; }
.acc-text   { color:var(--text)   !important; }
.acc-gold   { color:var(--gold)   !important; }
.acc-silver { color:var(--silver) !important; }
.acc-bronze { color:var(--bronze) !important; }
.bar-green  { background:var(--green)  !important; }
.bar-blue   { background:var(--blue)   !important; }
.bar-amber  { background:var(--amber)  !important; }
.bar-purple { background:var(--purple) !important; }
.bar-red    { background:var(--red)    !important; }

/* ── Signal cards ── */
.card {
  background:linear-gradient(160deg,var(--card) 0%,#05101e 100%);
  border:1px solid var(--bdr); border-radius:16px;
  padding:16px 18px 12px; margin-bottom:2px;
  position:relative; overflow:hidden;
  transition:border-color 0.18s,transform 0.18s,box-shadow 0.18s;
}
.card:hover { border-color:var(--bdr2); transform:translateY(-2px); box-shadow:0 10px 30px rgba(0,0,0,0.35); }
.card::before { content:''; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,var(--bdr2),transparent); }
.card-sell { border-color:rgba(255,71,87,0.18) !important; }
.ch { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
.ch-left { display:flex; align-items:center; gap:12px; flex:1; min-width:0; }
.logo-wrap { width:40px; height:40px; border-radius:10px; background:var(--glass); border:1px solid var(--bdr); display:flex; align-items:center; justify-content:center; flex-shrink:0; overflow:hidden; }
.logo-wrap img { width:28px; height:28px; object-fit:contain; border-radius:4px; }
.logo-fb { font-family:var(--mono); font-size:0.7rem; color:var(--sub); font-weight:700; }
.t-sym { font-family:var(--mono); font-size:1.2rem; font-weight:700; line-height:1.1; }
.t-co  { font-size:0.65rem; color:var(--sub); margin-top:1px; }
.score-ring { font-family:var(--mono); font-size:0.9rem; font-weight:700; width:46px; height:46px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2px solid; flex-shrink:0; }
.badges { display:flex; gap:5px; flex-wrap:wrap; margin:8px 0 6px; }
.badge { font-family:var(--mono); font-size:0.54rem; letter-spacing:0.08em; padding:2px 7px; border-radius:4px; border:1px solid; }
.b-buy    { background:rgba(0,212,170,0.1);    border-color:rgba(0,212,170,0.3);   color:var(--green); }
.b-sell   { background:rgba(255,71,87,0.1);    border-color:rgba(255,71,87,0.3);   color:var(--red); }
.b-high   { background:rgba(0,212,170,0.08);   border-color:rgba(0,212,170,0.22);  color:var(--green); }
.b-medium { background:rgba(255,165,2,0.08);   border-color:rgba(255,165,2,0.22);  color:var(--amber); }
.b-low    { background:rgba(124,143,173,0.08); border-color:rgba(124,143,173,0.2); color:var(--sub); }
.pills { display:flex; flex-wrap:wrap; gap:4px; margin:6px 0 8px; }
.pill { font-size:0.58rem; color:var(--sub); background:rgba(255,255,255,0.03); border:1px solid var(--bdr); border-radius:4px; padding:2px 7px; font-family:var(--mono); }
.btrack { background:var(--bdr); border-radius:3px; height:2px; margin:6px 0 10px; position:relative; overflow:hidden; }
.stats { display:flex; gap:20px; margin-bottom:4px; }
.sl { font-size:0.54rem; color:var(--muted); letter-spacing:0.09em; text-transform:uppercase; margin-bottom:2px; }
.sv { font-family:var(--mono); font-size:0.8rem; color:var(--text); }
.card-done { opacity:0.28; pointer-events:none; }
.b-mirrored { font-family:var(--mono); font-size:0.54rem; padding:2px 7px; border-radius:4px; background:rgba(0,212,170,0.08); border:1px solid var(--green); color:var(--green); }
.b-skipped  { font-family:var(--mono); font-size:0.54rem; padding:2px 7px; border-radius:4px; background:rgba(255,71,87,0.08); border:1px solid var(--red); color:var(--red); }
.t-ok  { background:rgba(0,212,170,0.07); border:1px solid rgba(0,212,170,0.28); border-radius:10px; padding:9px 15px; font-size:0.7rem; color:var(--green); font-family:var(--mono); margin-bottom:7px; }
.t-err { background:rgba(255,71,87,0.07);  border:1px solid rgba(255,71,87,0.28);  border-radius:10px; padding:9px 15px; font-size:0.7rem; color:var(--red);   font-family:var(--mono); margin-bottom:7px; }
.sec-lbl { font-size:0.57rem; letter-spacing:0.17em; text-transform:uppercase; color:var(--muted); margin:18px 0 10px; padding-bottom:8px; border-bottom:1px solid var(--bdr); font-family:var(--mono); }
.ddl { font-size:0.53rem; letter-spacing:0.17em; text-transform:uppercase; color:var(--muted); margin:14px 0 7px; font-family:var(--mono); }
.bio-card { background:rgba(255,255,255,0.02); border:1px solid var(--bdr); border-radius:10px; padding:12px 15px; margin-bottom:7px; }
.bio-name { font-size:0.84rem; font-weight:600; color:var(--text); margin-bottom:2px; }
.bio-role { font-size:0.61rem; color:var(--sub); margin-bottom:7px; }
.bio-line { font-size:0.68rem; color:var(--sub); line-height:1.65; margin-bottom:3px; }
.bio-line strong { color:var(--text); }
.ai-box { background:rgba(0,212,170,0.03); border:1px solid rgba(0,212,170,0.13); border-radius:10px; padding:13px 15px; margin-top:10px; }
.ai-lbl  { font-size:0.53rem; letter-spacing:0.17em; text-transform:uppercase; color:var(--green); margin-bottom:7px; font-family:var(--mono); }
.ai-text { font-size:0.7rem; color:var(--sub); line-height:1.72; }
.pos-row { display:flex; justify-content:space-between; align-items:center; padding:13px 0; border-bottom:1px solid var(--bdr); }
.pos-sym  { font-family:var(--mono); font-size:0.96rem; font-weight:700; }
.pos-meta { font-size:0.61rem; color:var(--sub); margin-top:3px; }
[data-testid="metric-container"] { background:var(--glass) !important; border:1px solid var(--bdr) !important; border-radius:12px !important; padding:14px 18px !important; }
[data-testid="stMetricValue"]    { font-family:var(--mono) !important; font-size:1.2rem !important; font-weight:700 !important; color:var(--green) !important; }
[data-testid="stMetricLabel"]    { font-size:0.57rem !important; letter-spacing:0.14em !important; text-transform:uppercase !important; color:var(--sub) !important; }
div.stButton > button { width:100% !important; border-radius:8px !important; font-family:var(--mono) !important; font-size:0.68rem !important; letter-spacing:0.07em !important; padding:9px 12px !important; border:1px solid var(--bdr2) !important; background:var(--glass) !important; color:var(--sub) !important; transition:all 0.18s ease !important; }
div.stButton > button:hover { border-color:var(--green) !important; color:var(--green) !important; background:rgba(0,212,170,0.07) !important; transform:translateY(-1px) !important; }
div.stButton > button[kind="primary"] { background:rgba(0,212,170,0.1) !important; border-color:var(--green) !important; color:var(--green) !important; }
[data-testid="stExpander"] { background:var(--glass) !important; border:1px solid var(--bdr) !important; border-radius:10px !important; margin-top:-4px !important; margin-bottom:10px !important; }
[data-testid="stExpander"] summary { font-family:var(--mono) !important; font-size:0.65rem !important; letter-spacing:0.09em !important; color:var(--sub) !important; }
.lb-row { display:flex; align-items:center; gap:12px; background:var(--glass); border:1px solid var(--bdr); border-radius:12px; padding:10px 14px; margin-bottom:7px; transition:border-color 0.15s; }
.lb-row:hover { border-color:var(--bdr2); }
.lb-rank { font-family:var(--mono); font-size:0.67rem; color:var(--muted); min-width:26px; }
.lb-name { font-size:0.81rem; font-weight:500; color:var(--text); flex:1; }
.empty { text-align:center; padding:56px 20px; color:var(--muted); font-size:0.75rem; font-family:var(--mono); letter-spacing:0.05em; line-height:2.2; }
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] { background:var(--green) !important; border-color:var(--green) !important; }
/* Utility classes to avoid var() in inline HTML strings */
.price-val  { font-family:'Space Mono',monospace; font-size:1rem; font-weight:700; }
.price-chg  { font-family:'Space Mono',monospace; font-size:0.73rem; }
.price-row  { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px; }
.unavail    { font-size:0.67rem; color:#7c8fad; padding:6px 0; }
.about-body { font-size:0.71rem; color:#e2e8f0; line-height:1.72; margin-bottom:6px; }
.risk-row   { font-size:0.61rem; color:#7c8fad; }
.risk-bars  { font-family:'Space Mono',monospace; color:#e2e8f0; }
.date-hint  { font-size:0.55rem; margin-top:2px; color:#3a4a62; }
.pending-count { text-align:right; font-family:'Space Mono',monospace; font-size:0.76rem; padding-top:20px; }
.pos-pnl-main { font-family:'Space Mono',monospace; font-size:0.9rem; font-weight:600; }
.pos-pnl-pct  { font-family:'Space Mono',monospace; font-size:0.66rem; }
.pos-mkt      { font-size:0.59rem; color:#7c8fad; margin-top:1px; }
.pos-cat-tag  { font-size:0.55rem; font-family:'Space Mono',monospace; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07); border-radius:4px; padding:1px 5px; margin-left:6px; }
.lb-score-val { font-family:'Space Mono',monospace; font-size:0.79rem; }
.lb-pnl       { font-family:'Space Mono',monospace; font-size:0.66rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
CATEGORIES = {
    'politicians': {'label': 'Politicians',    'acc': 'green',  'hex': '#00d4aa', 'count': 8},
    'ceos':        {'label': 'Superinvestors', 'acc': 'blue',   'hex': '#38bdf8', 'count': 7},
    'athletes':    {'label': 'Athletes',       'acc': 'amber',  'hex': '#ffa502', 'count': 7},
    'sectors':     {'label': 'Sectors',        'acc': 'purple', 'hex': '#a78bfa', 'count': 7},
}
DECISIONS_FILE = HERE / 'decisions.json'
TRADE_LOG_FILE = HERE / 'trade_log.json'

# ─────────────────────────────────────────────
def load_decisions():
    try: return json.load(open(DECISIONS_FILE))
    except: return {}

def save_decisions(d):
    with open(DECISIONS_FILE, 'w') as f: json.dump(d, f)

def load_trade_log():
    try: return json.load(open(TRADE_LOG_FILE))
    except: return []

def append_trade_log(entry):
    log = load_trade_log(); log.append(entry)
    with open(TRADE_LOG_FILE, 'w') as f: json.dump(log, f, indent=2)

@st.cache_data(ttl=300)
def load_suggestions():
    try:
        data = json.load(open(HERE / 'suggestions.json'))
        if isinstance(data, list):
            return {'politicians': data, 'ceos': [], 'athletes': [], 'sectors': [], 'last_updated': None}
        return data
    except: return {'politicians': [], 'ceos': [], 'athletes': [], 'sectors': [], 'last_updated': None}

@st.cache_data(ttl=3600)
def fetch_price_history(symbol):
    key = os.getenv('ALPACA_KEY', ''); secret = os.getenv('ALPACA_SECRET', '')
    if not key: return []
    end = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    start = (datetime.now(timezone.utc) - timedelta(days=45)).strftime('%Y-%m-%d')
    try:
        r = _req.get('https://data.alpaca.markets/v2/stocks/' + symbol + '/bars',
            params={'timeframe':'1Day','start':start,'end':end,'limit':30,'feed':'iex'},
            headers={'APCA-API-KEY-ID':key,'APCA-API-SECRET-KEY':secret}, timeout=10)
        return [round(b['c'],2) for b in r.json().get('bars',[])] if r.ok else []
    except: return []

def logo_url(ticker):
    d = TICKER_DOMAIN.get(ticker, '')
    return ('https://www.google.com/s2/favicons?domain=' + d + '&sz=64') if d else ''

@st.cache_resource
def get_client():
    k = os.getenv('ALPACA_KEY'); s = os.getenv('ALPACA_SECRET')
    if not k or not s: return None
    return TradingClient(k, s, paper=True)

@st.cache_data(ttl=60)
def load_account():
    c = get_client()
    if not c: return None
    try: return c.get_account()
    except: return None

@st.cache_data(ttl=60)
def load_positions():
    c = get_client()
    if not c: return []
    try: return c.get_all_positions()
    except: return []

def get_trade_notional(pct=None):
    if pct is None: pct = st.session_state.get('trade_pct', 0.5)
    acct = load_account()
    equity = float(acct.equity) if acct else 100000.0
    return max(10.0, round(equity * pct / 100.0, 2))

def place_order(symbol, side=OrderSide.BUY, category='', investors=''):
    client = get_client()
    if not client: return False, "Alpaca not configured", None
    notional = get_trade_notional()
    try:
        if side == OrderSide.SELL:
            positions = load_positions()
            pos = next((p for p in positions if p.symbol == symbol), None)
            if not pos: return False, "No open position in " + symbol, None
            req = MarketOrderRequest(symbol=symbol, qty=float(pos.qty), side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
        else:
            req = MarketOrderRequest(symbol=symbol, notional=notional, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
        order = client.submit_order(req)
        import time as _t; _t.sleep(1.5)
        try: o = client.get_order_by_id(order.id); status = str(o.status).split('.')[-1].lower()
        except: status = 'submitted'
        append_trade_log({'ticker':symbol,'side':'sell' if side==OrderSide.SELL else 'buy',
            'category':category,'investors':investors,'notional':notional,
            'order_id':str(order.id),'status':status,'timestamp':datetime.now(timezone.utc).isoformat()})
        return True, str(order.id)[:8] + ' ' + status, notional
    except Exception as e: return False, str(e), None

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in [('tab','feed'),('category','politicians'),('toasts',[]),('trade_pct',0.5)]:
    if k not in st.session_state: st.session_state[k] = v
if 'decisions' not in st.session_state: st.session_state.decisions = load_decisions()

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30*60*1000, key='ar')
except ImportError: pass

_notional = get_trade_notional()
_pct      = st.session_state.trade_pct

# ─────────────────────────────────────────────
# TOPBAR + DRAWER via st.components.v1.html()
# This renders in its own sub-iframe with no HTML sanitization — input/label/
# JS all work. Navigation is communicated back via URL query params set by JS
# on the parent window.
# ─────────────────────────────────────────────
import streamlit.components.v1 as _components

sug = load_suggestions()
lu  = sug.get('last_updated')
fresh = 'No data'
if lu:
    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(lu)
        h = int(age.total_seconds() // 3600)
        fresh = (str(h) + 'h ago') if h < 24 else (str(age.days) + 'd ago')
    except: pass

acct = load_account()
eq_str = '$100,000'; bp_str = '$200,000'; pnl_str2 = '+$0.00'; pnl_col = '#00d4aa'
if acct:
    eq  = float(acct.equity)
    bp  = float(acct.buying_power)
    pnl = eq - float(acct.last_equity)
    pnl_col  = '#00d4aa' if pnl >= 0 else '#ff4757'
    eq_str   = '$' + '{:,.0f}'.format(eq)
    bp_str   = '$' + '{:,.0f}'.format(bp)
    pnl_str2 = ('+' if pnl >= 0 else '') + '$' + '{:,.2f}'.format(abs(pnl))

notional_str = '$' + '{:,.0f}'.format(_notional) + ' (' + '{:.1f}'.format(_pct) + '%)'

_topbar_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&family=Space+Mono:wght@400;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
html,body{height:56px;overflow:hidden;background:#04080f;}
#topbar{
  height:56px;background:rgba(4,8,15,0.97);
  border-bottom:1px solid rgba(255,255,255,0.08);
  display:flex;align-items:center;padding:0 16px;gap:12px;
}
#logo{
  font-family:'Space Mono',monospace;font-size:.95rem;font-weight:700;
  letter-spacing:.22em;margin-right:auto;color:#00d4aa;
}
#chip{
  font-family:'Space Mono',monospace;font-size:.6rem;letter-spacing:.05em;
  padding:5px 12px;border-radius:6px;
  background:rgba(0,212,170,.07);border:1px solid rgba(0,212,170,.22);
  color:#00d4aa;white-space:nowrap;
}
.pnl{font-size:.55rem;opacity:.8;color:PNL_COL;}
</style>
</head>
<body>
<div id="topbar">
  <div id="logo">MIRROR AI</div>
  <div id="chip">EQ_STR &nbsp;<span class="pnl">PNL_STR</span></div>
</div>
</body>
</html>"""

_topbar_html = _topbar_html.replace('EQ_STR', eq_str)
_topbar_html = _topbar_html.replace('PNL_STR', pnl_str2)
_topbar_html = _topbar_html.replace('PNL_COL', pnl_col)
tab_now = st.session_state.tab
cat_now = st.session_state.category
# (no other replacements needed — drawer is now in Streamlit sidebar)
_topbar_html = _topbar_html.replace('NAV_POS',  'active' if tab_now == 'positions' else '')
_components.html(_topbar_html, height=56, scrolling=False)

# ─────────────────────────────────────────────
# SIDEBAR — styled as the slide-in drawer (Streamlit native, no iframe issues)
# User opens it with the Streamlit arrow button (top-left of sidebar)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    # Portfolio card
    if acct:
        st.markdown(
            '<div class="port-card">'
            '<div class="port-lbl">Portfolio</div>'
            '<div class="port-eq">' + eq_str + '</div>'
            '<div class="port-row"><span>Buying power</span><span class="drw-val">' + bp_str + '</span></div>'
            '<div class="port-row"><span>Today P&L</span><span class="drw-val ' + ('acc-green' if pnl >= 0 else 'acc-red') + '">' + pnl_str2 + '</span></div>'
            '<div class="port-row"><span>Trade size</span><span class="drw-val acc-green">' + notional_str + '</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:4px;border-top:1px solid rgba(255,255,255,0.07);margin:4px 0"></div>', unsafe_allow_html=True)

    for tk, tl in [('feed', 'Signal Feed'), ('positions', 'Positions'), ('leaderboard', 'Leaderboard')]:
        if st.button(tl, key='nav_' + tk, use_container_width=True,
                     type='primary' if st.session_state.tab == tk else 'secondary'):
            st.session_state.tab = tk; st.rerun()

    if st.session_state.tab == 'feed':
        st.markdown('<div style="height:4px;border-top:1px solid rgba(255,255,255,0.07);margin:8px 0 4px"></div>', unsafe_allow_html=True)
        for ck, ci in CATEGORIES.items():
            dot = '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:' + ci['hex'] + ';margin-right:8px;vertical-align:middle"></span>'
            if st.button(dot + ci['label'], key='cat_' + ck, use_container_width=True,
                         type='primary' if st.session_state.category == ck else 'secondary'):
                st.session_state.category = ck; st.rerun()

    st.markdown('<div style="height:4px;border-top:1px solid rgba(255,255,255,0.07);margin:8px 0 4px"></div>', unsafe_allow_html=True)
    new_pct = st.slider('Trade %', 0.1, 5.0, float(_pct), 0.1, format='%.1f%%')
    if new_pct != _pct:
        st.session_state.trade_pct = new_pct; _notional = get_trade_notional(new_pct); st.rerun()

    st.markdown('<div style="font-size:0.55rem;color:#3a4a62;font-family:Space Mono,monospace;padding:4px 0">Data: ' + fresh + '</div>', unsafe_allow_html=True)
    if st.button('Refresh data', key='refresh', use_container_width=True):
        st.cache_data.clear(); st.rerun()

# Tab buttons in main area
tab_col1, tab_col2, tab_col3, spacer = st.columns([1, 1, 1, 4])
with tab_col1:
    if st.button('Feed', key='mt_feed', use_container_width=True,
                 type='primary' if st.session_state.tab == 'feed' else 'secondary'):
        st.session_state.tab = 'feed'; st.rerun()
with tab_col2:
    if st.button('Positions', key='mt_pos', use_container_width=True,
                 type='primary' if st.session_state.tab == 'positions' else 'secondary'):
        st.session_state.tab = 'positions'; st.rerun()
with tab_col3:
    if st.button('Leaderboard', key='mt_lb', use_container_width=True,
                 type='primary' if st.session_state.tab == 'leaderboard' else 'secondary'):
        st.session_state.tab = 'leaderboard'; st.rerun()

if st.session_state.tab == 'feed':
    cc = st.columns(len(CATEGORIES))
    for i, (ck, ci) in enumerate(CATEGORIES.items()):
        with cc[i]:
            if st.button(ci['label'], key='mcat_' + ck, use_container_width=True,
                         type='primary' if st.session_state.category == ck else 'secondary'):
                st.session_state.category = ck; st.rerun()

# ─────────────────────────────────────────────
# TOASTS
# ─────────────────────────────────────────────
for ok, msg in st.session_state.toasts:
    st.markdown('<div class="' + ('t-ok' if ok else 't-err') + '">' + msg + '</div>', unsafe_allow_html=True)
st.session_state.toasts = []

tab = st.session_state.tab
cat = st.session_state.category

# ─────────────────────────────────────────────
# SIGNAL CARD
# ─────────────────────────────────────────────
def render_signal_card(s, cat_key, acc, key_prefix, notional):
    ticker     = s.get('ticker', '')
    score      = float(s.get('score', 0))
    conviction = int(s.get('conviction', 1))
    investors  = s.get('investors', '')
    buy_count  = int(s.get('buy_count', conviction))
    action     = s.get('action', 'BUY')
    is_sell    = action == 'SELL'
    total      = CATEGORIES[cat_key]['count']
    bar_pct    = min(100, int((conviction / total) * 100))
    conf_lbl, _ = confidence_label(conviction, total, score)
    profile    = TICKER_PROFILES.get(ticker, {})
    data_as_of = s.get('data_as_of', '')

    ticker_acc = 'acc-red' if is_sell else 'acc-' + acc
    ring_cls   = 'acc-red' if is_sell else 'acc-' + acc
    bar_cls    = 'bar-red' if is_sell else 'bar-' + acc
    a_cls      = 'b-sell' if is_sell else 'b-buy'
    conf_cls   = 'b-' + conf_lbl.lower()

    lurl = logo_url(ticker)
    if lurl:
        logo_html = (
            '<div class="logo-wrap">'
            '<img src="' + lurl + '" alt="" width="28" height="28" '
            'onerror="this.style.display=\'none\';this.nextSibling.style.display=\'block\'">'
            '<span class="logo-fb" style="display:none">' + ticker[:2] + '</span>'
            '</div>'
        )
    else:
        logo_html = '<div class="logo-wrap"><span class="logo-fb">' + ticker[:2] + '</span></div>'

    company  = profile.get('company', '') or ''
    sector   = profile.get('sector', '') or ''
    co_line  = company + ('  &middot;  ' + sector if sector else '')
    inv_list = [p.strip() for p in investors.split(',') if p.strip()]
    pills    = ''.join('<span class="pill">' + p + '</span>' for p in inv_list)
    date_ln  = ('<div class="date-hint">as of ' + data_as_of + '</div>') if data_as_of else ''

    st.markdown(
        '<div class="card' + (' card-sell' if is_sell else '') + '">'
        '<div class="ch">'
          '<div class="ch-left">'
            + logo_html +
            '<div><div class="t-sym ' + ticker_acc + '">' + ticker + '</div>'
            '<div class="t-co">' + co_line + '</div>' + date_ln + '</div>'
          '</div>'
          '<div class="score-ring ' + ring_cls + '">' + '{:.1f}'.format(score) + '</div>'
        '</div>'
        '<div class="badges">'
          '<span class="badge ' + a_cls + '">' + action + '</span>'
          '<span class="badge ' + conf_cls + '">' + conf_lbl + '</span>'
        '</div>'
        '<div class="pills">' + pills + '</div>'
        '<div class="btrack"><div class="' + bar_cls + '" style="position:absolute;top:0;left:0;height:2px;border-radius:3px;opacity:0.8;width:' + str(bar_pct) + '%"></div></div>'
        '<div class="stats">'
          '<div><div class="sl">Conviction</div><div class="sv">' + str(conviction) + '/' + str(total) + '</div></div>'
          '<div><div class="sl">Disclosures</div><div class="sv">' + str(buy_count) + '</div></div>'
          '<div><div class="sl">Score</div><div class="sv ' + ticker_acc + '">' + '{:.2f}'.format(score) + '</div></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander('Deep dive  ' + ticker, expanded=False):
        bars = fetch_price_history(ticker)
        if bars:
            pct_chg = ((bars[-1] - bars[0]) / bars[0] * 100) if bars[0] else 0
            chg_cls = 'acc-green' if pct_chg >= 0 else 'acc-red'
            st.markdown(
                '<div class="price-row">'
                '<span class="price-val ' + ring_cls + '">$' + '{:,.2f}'.format(bars[-1]) + '</span>'
                '<span class="price-chg ' + chg_cls + '">' + '{:+.1f}'.format(pct_chg) + '% &nbsp;30d</span>'
                '</div>', unsafe_allow_html=True)
            st.line_chart({'Price': bars}, height=90, use_container_width=True)
        else:
            st.markdown('<div class="unavail">Price history unavailable</div>', unsafe_allow_html=True)
        if profile:
            risk = profile.get('risk', 3)
            st.markdown(
                '<div class="ddl">About ' + ticker + '</div>'
                '<div class="about-body">' + profile.get('summary','') + '</div>'
                '<div class="risk-row">Risk <span class="risk-bars">' + chr(9608)*risk + chr(9617)*(5-risk) + '</span> ' + str(risk) + '/5</div>',
                unsafe_allow_html=True)
        inv_list2 = [p.strip() for p in investors.split(',') if p.strip()]
        if inv_list2:
            st.markdown('<div class="ddl">Who is behind this signal</div>', unsafe_allow_html=True)
            for trader in inv_list2:
                bio = TRADER_BIOS.get(trader, {})
                if bio:
                    st.markdown(
                        '<div class="bio-card">'
                        '<div class="bio-name">' + trader + '</div>'
                        '<div class="bio-role">' + bio.get('role','') + '</div>'
                        '<div class="bio-line"><strong>Track record:</strong> ' + bio.get('track_record','') + '</div>'
                        '<div class="bio-line"><strong>Style:</strong> ' + bio.get('style','') + '</div>'
                        '<div class="bio-line"><strong>Notable:</strong> ' + bio.get('notable','') + '</div>'
                        '</div>', unsafe_allow_html=True)
        reasoning = SCORING_EXPLAINER.get(cat_key, '')
        if reasoning:
            st.markdown(
                '<div class="ai-box"><div class="ai-lbl">Why Mirror AI picked this</div>'
                '<div class="ai-text">' + reasoning + '</div></div>',
                unsafe_allow_html=True)

    decision_key = cat_key + '_' + ticker + '_' + action
    col_a, col_b = st.columns([3, 2])
    with col_a:
        btn_lbl = ('MIRROR  SELL  ' + ticker) if is_sell else ('MIRROR  BUY  $' + '{:,.0f}'.format(notional) + '  (' + '{:.1f}'.format(_pct) + '%)')
        if st.button(btn_lbl, key=key_prefix+'_a', use_container_width=True, type='primary'):
            ok, result, amt = place_order(ticker, side=OrderSide.SELL if is_sell else OrderSide.BUY, category=cat_key, investors=investors)
            st.session_state.decisions[decision_key] = 'mirrored'
            save_decisions(st.session_state.decisions)
            verb = 'Sold' if is_sell else 'Bought'
            st.session_state.toasts.append((ok, (verb+': '+ticker+' '+result) if ok else 'Order failed: '+result))
            st.rerun()
    with col_b:
        if st.button('SKIP', key=key_prefix+'_b', use_container_width=True):
            st.session_state.decisions[decision_key] = 'skipped'
            save_decisions(st.session_state.decisions)
            st.rerun()
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FEED
# ─────────────────────────────────────────────
if tab == 'feed':
    acc     = CATEGORIES[cat]['acc']
    signals = sug.get(cat, [])
    pending = [s for s in signals if st.session_state.decisions.get(cat+'_'+s['ticker']+'_'+s.get('action','BUY'),'pending') == 'pending']
    decided = [s for s in signals if st.session_state.decisions.get(cat+'_'+s['ticker']+'_'+s.get('action','BUY'),'pending') != 'pending']

    c1, c2 = st.columns([4, 1])
    with c1: st.markdown('<div class="sec-lbl">'+CATEGORIES[cat]['label']+'  &middot;  Signal Feed</div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="pending-count acc-'+acc+'">'+str(len(pending))+' pending</div>', unsafe_allow_html=True)

    if not signals: st.markdown('<div class="empty">No signals yet<br>Run fetcher.py to pull latest data</div>', unsafe_allow_html=True)
    elif not pending: st.markdown('<div class="empty">All signals reviewed<br>Check back after next refresh</div>', unsafe_allow_html=True)

    for i, s in enumerate(pending):
        render_signal_card(s, cat, acc, 'p_'+cat+'_'+str(i), _notional)

    if decided:
        st.markdown('<div class="sec-lbl">Reviewed  &middot;  '+str(len(decided))+'</div>', unsafe_allow_html=True)
        for s in decided:
            ticker = s.get('ticker',''); action = s.get('action','BUY')
            dec    = st.session_state.decisions.get(cat+'_'+ticker+'_'+action,'')
            badge  = '<span class="b-mirrored">MIRRORED</span>' if dec=='mirrored' else '<span class="b-skipped">SKIPPED</span>'
            acc_c  = 'acc-red' if action=='SELL' else 'acc-'+acc
            a_cls  = 'b-sell' if action=='SELL' else 'b-buy'
            st.markdown('<div class="card card-done" style="padding:10px 18px"><div style="display:flex;justify-content:space-between;align-items:center"><div style="display:flex;align-items:center;gap:8px"><span class="t-sym '+acc_c+'" style="font-size:0.93rem">'+ticker+'</span><span class="badge '+a_cls+'">'+action+'</span></div>'+badge+'</div></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# POSITIONS
# ─────────────────────────────────────────────
elif tab == 'positions':
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
        with c1: st.metric('Portfolio value', '$'+'{:,.2f}'.format(total_val))
        with c2: st.metric('Unrealized P&L',  '$'+'{:+,.2f}'.format(total_pnl))
        st.markdown('<br>', unsafe_allow_html=True)
        for p in sorted(positions, key=lambda x: float(x.unrealized_pl), reverse=True):
            pnl = float(p.unrealized_pl); pct = float(p.unrealized_plpc)*100; mval = float(p.market_value)
            pnl_cls = 'acc-green' if pnl >= 0 else 'acc-red'
            log = log_by_sym.get(p.symbol, {}); c = log.get('category',''); inv = log.get('investors','')
            cat_hex = CATEGORIES.get(c,{}).get('hex','')
            cat_acc_cls = CATEGORIES.get(c, {}).get('acc', '')
            cat_tag = ('<span class="pos-cat-tag acc-'+cat_acc_cls+'">'+c.upper()+'</span>') if c and cat_acc_cls else ''
            lurl = logo_url(p.symbol)
            logo_bit = '<img src="'+lurl+'" style="width:20px;height:20px;border-radius:5px;margin-right:7px;vertical-align:middle" onerror="this.style.display=\'none\'" alt="">' if lurl else ''
            st.markdown('<div class="pos-row"><div><div class="pos-sym">'+logo_bit+p.symbol+cat_tag+'</div><div class="pos-meta">'+'{:.4f}'.format(float(p.qty))+' sh &middot; $'+'{:,.2f}'.format(float(p.current_price))+' &middot; '+(inv[:35] or '—')+'</div></div><div style="text-align:right"><div class="pos-pnl-main '+pnl_cls+'">$'+'{:+,.2f}'.format(pnl)+'</div><div class="pos-pnl-pct '+pnl_cls+'">'+'{:+.2f}'.format(pct)+'%</div><div class="pos-mkt">$'+'{:,.2f}'.format(mval)+' mkt</div></div></div>', unsafe_allow_html=True)
    st.markdown('<br>', unsafe_allow_html=True)
    if st.button('Refresh positions', use_container_width=True): st.cache_data.clear(); st.rerun()


# ─────────────────────────────────────────────
# LEADERBOARD
# ─────────────────────────────────────────────
elif tab == 'leaderboard':
    positions  = load_positions(); trade_log = load_trade_log()
    pnl_by_sym = {p.symbol: float(p.unrealized_pl) for p in positions}
    cat_pnl    = {}
    for entry in trade_log:
        c = entry.get('category',''); sym = entry.get('ticker','')
        if c and sym in pnl_by_sym: cat_pnl[c] = cat_pnl.get(c,0.0) + pnl_by_sym[sym]
    st.markdown('<div class="sec-lbl">Leaderboard  &middot;  Signal strength by source</div>', unsafe_allow_html=True)
    for cat_key, cat_info in CATEGORIES.items():
        acc = cat_info['acc']; signals = sug.get(cat_key,[])
        if not signals: continue
        pnl = cat_pnl.get(cat_key); pnl_str = ''
        if pnl is not None:
            pnl_cls = 'acc-green' if pnl >= 0 else 'acc-red'
            pnl_str = '  <span class="lb-pnl '+pnl_cls+'">$'+'{:+,.2f}'.format(pnl)+'</span>'
        holder_scores: dict = {}
        for sg in signals:
            for inv in sg.get('investors','').split(','):
                inv = inv.strip()
                if inv: holder_scores[inv] = holder_scores.get(inv,0.0) + float(sg.get('score',0))
        ranked = sorted(holder_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = ranked[0][1] if ranked else 1.0
        st.markdown('<div class="sec-lbl">'+cat_info['label'].upper()+pnl_str+'</div>', unsafe_allow_html=True)
        rank_classes = ['acc-gold','acc-silver','acc-bronze']
        for i, (name, score) in enumerate(ranked[:7]):
            bar_pct = int((score/max_score)*100); rank_cls = rank_classes[i] if i < 3 else 'acc-muted'
            st.markdown('<div class="lb-row"><span class="lb-rank '+rank_cls+'">#'+'{:02d}'.format(i+1)+'</span><div style="flex:1"><div class="lb-name">'+name+'</div><div class="btrack" style="margin:4px 0 0"><div class="bar-'+acc+'" style="position:absolute;top:0;left:0;height:2px;border-radius:2px;opacity:0.65;width:'+str(bar_pct)+'%"></div></div></div><span class="lb-score-val acc-'+acc+'">'+'{:.1f}'.format(score)+'</span></div>', unsafe_allow_html=True)
    st.markdown('<br>', unsafe_allow_html=True)
    if st.button('Refresh all data', use_container_width=True): st.cache_data.clear(); st.rerun()
