import streamlit as st
import json
import os
from pathlib import Path
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

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

@st.cache_resource
def get_client():
    k = os.getenv('ALPACA_KEY')
    s = os.getenv('ALPACA_SECRET')
    if not k or not s:
        return None
    return TradingClient(k, s, paper=True)

def place_order(symbol, notional=500):
    client = get_client()
    if not client:
        return False, "Alpaca credentials not configured"
    try:
        req = MarketOrderRequest(
            symbol=symbol, notional=notional,
            side=OrderSide.BUY, time_in_force=TimeInForce.DAY
        )
        order = client.submit_order(req)
        return True, str(order.id)
    except Exception as e:
        return False, str(e)

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

@st.cache_data(ttl=300)
def load_suggestions():
    try:
        with open(HERE / 'suggestions.json') as f:
            data = json.load(f)
        # Support both old flat list and new dict-of-categories format
        if isinstance(data, list):
            return {'politicians': data, 'ceos': [], 'athletes': [], 'sectors': []}
        return data
    except Exception:
        return {'politicians': [], 'ceos': [], 'athletes': [], 'sectors': []}


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

for key, default in [
    ('tab', 'feed'),
    ('category', 'politicians'),
    ('decisions', {}),
    ('toasts', []),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown('<div class="wordmark">MIRROR AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Paper trading &nbsp;·&nbsp; Signal intelligence</div>', unsafe_allow_html=True)

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

        bar_cls = 'bar-fill' if conviction >= 3 else ('bar-fill-amber' if conviction == 2 else 'bar-fill-low')
        pills   = ''.join(f'<span class="pill">{p.strip()}</span>' for p in investors.split(',') if p.strip())

        st.markdown(f"""
        <div class="card">
          <div class="card-top">
            <div class="ticker-wrap">
              <span class="ticker" style="color:{accent}">{ticker}</span>
              <span class="side-tag">BUY</span>
            </div>
            <span class="score-badge" style="color:{accent};border-color:{accent}33;background:{accent}0a">{score:.2f}</span>
          </div>
          <div class="holder-pills">{pills}</div>
          <div class="bar-track"><div class="{bar_cls}" style="width:{bar_pct}%;background:{accent}"></div></div>
          <div class="stats">
            <div class="stat">
              <div class="stat-label">Conviction</div>
              <div class="stat-val">{conviction} / {total}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Disclosures</div>
              <div class="stat-val">{buy_count}</div>
            </div>
            <div class="stat">
              <div class="stat-label">Signal</div>
              <div class="stat-val">{score:.1f}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        btn_a, btn_r = st.columns([3, 2])
        with btn_a:
            if st.button(f"APPROVE  $500", key=f"approve_{cat}_{ticker}", use_container_width=True):
                ok, result = place_order(ticker, 500)
                st.session_state.decisions[f"{cat}_{ticker}"] = 'approved'
                if ok:
                    st.session_state.toasts.append((True, f"Order placed: {ticker}  ·  ${500}  ·  id {result[:8]}"))
                else:
                    st.session_state.toasts.append((False, f"Order failed: {result}"))
                st.rerun()
        with btn_r:
            if st.button("REJECT", key=f"reject_{cat}_{ticker}", use_container_width=True):
                st.session_state.decisions[f"{cat}_{ticker}"] = 'rejected'
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
