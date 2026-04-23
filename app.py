import streamlit as st
import json
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

st.set_page_config(page_title="MIRROR AI", page_icon="M", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');
:root{--bg:#080808;--surface:#111111;--border:#1e1e1e;--green:#00ff87;--red:#ff3b5c;--muted:#444;--text:#e8e8e8;--subtext:#888;}
html,body,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--text)!important;font-family:'DM Sans',sans-serif!important;}
[data-testid="stAppViewContainer"]{max-width:480px;margin:0 auto;padding:0 12px;}
[data-testid="stHeader"]{background:var(--bg)!important;}
[data-testid="stMetricValue"]{font-family:'Space Mono',monospace!important;color:var(--green)!important;font-size:1.4rem!important;}
[data-testid="stMetricLabel"]{color:var(--subtext)!important;font-size:0.7rem!important;letter-spacing:0.1em;text-transform:uppercase;}
div.stButton>button{width:100%;border-radius:4px;font-family:'Space Mono',monospace;font-size:0.8rem;padding:10px;border:none;cursor:pointer;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:12px;}
.card-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;}
.ticker{font-family:'Space Mono',monospace;font-size:1.1rem;font-weight:700;color:var(--green);}
.company-name{font-size:0.75rem;color:var(--subtext);margin-top:2px;}
.score-badge{background:#0a1a0a;border:1px solid #1a3a1a;border-radius:4px;padding:4px 8px;font-family:'Space Mono',monospace;font-size:0.75rem;color:var(--green);}
.investor-pills{display:flex;flex-wrap:wrap;gap:4px;margin:8px 0;}
.pill{background:#161616;border:1px solid var(--border);border-radius:3px;padding:2px 7px;font-size:0.65rem;color:var(--subtext);text-transform:uppercase;letter-spacing:0.08em;}
.conviction-bar-bg{background:var(--border);border-radius:2px;height:3px;margin:8px 0;}
.conviction-bar{height:3px;border-radius:2px;background:var(--green);}
.stat-row{display:flex;justify-content:space-between;font-size:0.72rem;color:var(--subtext);margin-top:6px;}
.stat-val{color:var(--text);font-family:'Space Mono',monospace;}
.section-title{font-size:0.65rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin:20px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border);}
.approved-badge{background:#0a1a0a;border:1px solid var(--green);color:var(--green);font-family:'Space Mono',monospace;font-size:0.6rem;padding:2px 6px;border-radius:3px;}
.rejected-badge{background:#1a0a0a;border:1px solid var(--red);color:var(--red);font-family:'Space Mono',monospace;font-size:0.6rem;padding:2px 6px;border-radius:3px;}
.position-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--border);}
.pnl-pos{color:var(--green);font-family:'Space Mono',monospace;font-size:0.78rem;}
.pnl-neg{color:var(--red);font-family:'Space Mono',monospace;font-size:0.78rem;}
.header-logo{font-family:'Space Mono',monospace;font-size:1.0rem;font-weight:700;letter-spacing:0.2em;color:var(--green);text-align:center;padding:16px 0 4px;}
.header-sub{font-size:0.65rem;color:var(--muted);text-align:center;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:16px;}
.empty-state{text-align:center;padding:40px 20px;color:var(--muted);font-size:0.8rem;}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    return TradingClient(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), paper=True)

def place_order(symbol, notional=500):
    try:
        req = MarketOrderRequest(symbol=symbol, notional=notional, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
        order = get_client().submit_order(req)
        return True, str(order.id)
    except Exception as e:
        return False, str(e)

@st.cache_data(ttl=300)
def load_suggestions():
    try:
        with open('/home/ubuntu/suggestions.json') as f:
            return json.load(f)
    except:
        return []

@st.cache_data(ttl=60)
def load_account():
    try:
        return get_client().get_account()
    except:
        return None

@st.cache_data(ttl=60)
def load_positions():
    try:
        return get_client().get_all_positions()
    except:
        return []

if 'decisions' not in st.session_state:
    st.session_state.decisions = {}
if 'tab' not in st.session_state:
    st.session_state.tab = 'feed'

st.markdown('<div class="header-logo">MIRROR AI</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Paper trading · 7 investors</div>', unsafe_allow_html=True)

account = load_account()
if account:
    c1,c2,c3 = st.columns(3)
    c1.metric("Balance", f"${float(account.equity):,.0f}")
    c2.metric("Buying power", f"${float(account.buying_power):,.0f}")
    c3.metric("Today", f"${float(account.equity)-float(account.last_equity):+,.0f}")

t1,t2,t3 = st.columns(3)
with t1:
    if st.button("FEED", use_container_width=True, type="primary" if st.session_state.tab=='feed' else "secondary"):
        st.session_state.tab='feed'; st.rerun()
with t2:
    if st.button("POSITIONS", use_container_width=True, type="primary" if st.session_state.tab=='positions' else "secondary"):
        st.session_state.tab='positions'; st.rerun()
with t3:
    if st.button("LEADERBOARD", use_container_width=True, type="primary" if st.session_state.tab=='leaderboard' else "secondary"):
        st.session_state.tab='leaderboard'; st.rerun()

suggestions = load_suggestions()

if st.session_state.tab == 'feed':
    pending = [s for s in suggestions if st.session_state.decisions.get(s['name'],'pending')=='pending']
    decided = [s for s in suggestions if st.session_state.decisions.get(s['name'],'pending')!='pending']
    if not pending:
        st.markdown('<div class="empty-state">NO PENDING SUGGESTIONS<br>Run scorer.py to refresh signals</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-title">{len(pending)} pending signals</div>', unsafe_allow_html=True)
    for s in pending:
        name=s.get('name',''); score=float(s.get('score',0)); conviction=int(s.get('conviction',1))
        investors=s.get('investors',''); val_k=int(s.get('total_value_k',0))
        bar_pct=min(100,int((conviction/7)*100))
        pills=''.join([f'<span class="pill">{i.strip().title()}</span>' for i in investors.split(',')])
        st.markdown(f"""<div class="card">
            <div class="card-header"><div><div class="ticker">BUY</div><div class="company-name">{name}</div></div><div class="score-badge">{score:.1f}</div></div>
            <div class="investor-pills">{pills}</div>
            <div class="conviction-bar-bg"><div class="conviction-bar" style="width:{bar_pct}%"></div></div>
            <div class="stat-row"><span>Conviction</span><span class="stat-val">{conviction}/7 investors</span></div>
            <div class="stat-row"><span>Combined value</span><span class="stat-val">${val_k:,}k</span></div>
        </div>""", unsafe_allow_html=True)
        ca,cr=st.columns(2)
        with ca:
            if st.button(f"APPROVE $500", key=f"a_{name}", use_container_width=True):
                st.session_state.decisions[name]='approved'; st.rerun()
        with cr:
            if st.button("REJECT", key=f"r_{name}", use_container_width=True):
                st.session_state.decisions[name]='rejected'; st.rerun()
    if decided:
        st.markdown(f'<div class="section-title">{len(decided)} reviewed</div>', unsafe_allow_html=True)
        for s in decided:
            name=s.get('name',''); decision=st.session_state.decisions.get(name,'')
            badge='<span class="approved-badge">APPROVED</span>' if decision=='approved' else '<span class="rejected-badge">REJECTED</span>'
            st.markdown(f'<div class="card" style="opacity:0.5"><div class="card-header"><span style="font-size:0.85rem;color:var(--text)">{name}</span>{badge}</div></div>', unsafe_allow_html=True)

elif st.session_state.tab == 'positions':
    positions=load_positions()
    if not positions:
        st.markdown('<div class="empty-state">NO OPEN POSITIONS<br>Approve trades in the feed</div>', unsafe_allow_html=True)
    else:
        total_pnl=sum(float(p.unrealized_pl) for p in positions)
        cls='pnl-pos' if total_pnl>=0 else 'pnl-neg'
        st.markdown(f'<div class="section-title">Unrealized P&L: <span class="{cls}">${total_pnl:+,.2f}</span></div>', unsafe_allow_html=True)
        for p in sorted(positions, key=lambda x: float(x.unrealized_pl), reverse=True):
            pnl=float(p.unrealized_pl); pct=float(p.unrealized_plpc)*100
            cls='pnl-pos' if pnl>=0 else 'pnl-neg'
            st.markdown(f"""<div class="position-row">
                <div><div style="font-family:'Space Mono',monospace;font-size:0.9rem">{p.symbol}</div>
                <div style="font-size:0.7rem;color:var(--subtext)">{float(p.qty):.2f} shares · ${float(p.current_price):,.2f}</div></div>
                <div style="text-align:right"><div class="{cls}">${pnl:+,.2f}</div><div class="{cls}" style="font-size:0.7rem">{pct:+.2f}%</div></div>
            </div>""", unsafe_allow_html=True)

elif st.session_state.tab == 'leaderboard':
    investor_scores={}
    for s in suggestions:
        for inv in s.get('investors','').split(','):
            inv=inv.strip()
            if inv: investor_scores[inv]=investor_scores.get(inv,0)+float(s.get('score',0))
    ranked=sorted(investor_scores.items(),key=lambda x:x[1],reverse=True)
    max_score=ranked[0][1] if ranked else 1
    st.markdown('<div class="section-title">Signal strength by investor</div>', unsafe_allow_html=True)
    for i,(inv,score) in enumerate(ranked):
        bar_pct=int((score/max_score)*100)
        st.markdown(f"""<div class="card">
            <div class="card-header"><div style="font-family:'Space Mono',monospace;font-size:0.85rem;color:var(--text)">{str(i+1).zfill(2)}. {inv.upper()}</div><div class="score-badge">{score:.1f}</div></div>
            <div class="conviction-bar-bg"><div class="conviction-bar" style="width:{bar_pct}%"></div></div>
        </div>""", unsafe_allow_html=True)
    if st.button("REFRESH DATA", use_container_width=True):
        st.cache_data.clear(); st.rerun()
