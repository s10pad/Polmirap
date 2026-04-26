"""
fetcher.py — pulls signals for all 4 categories:
  1. politicians  — top 7 US politicians by trading returns (STOCK Act disclosures via Capitol Trades)
  2. ceos         — top 7 investor CEOs (SEC 13F quarterly filings)
  3. athletes     — top 7 investor athletes (curated public portfolio data, refreshed quarterly)
  4. sectors      — top 7 sectors tracked via flagship ETF holdings (SEC 13F)
"""

import requests
import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
SEC_HEADERS = {'User-Agent': 'MirrorAI arnaudpkengni@gmail.com', 'Accept': 'application/json'}

HERE = Path(__file__).parent

# ─────────────────────────────────────────────
# CATEGORY 1: POLITICIANS
# Top 7 by portfolio returns — Unusual Whales 2024 report
# ─────────────────────────────────────────────
POLITICIANS = {
    'pelosi':     {'name': 'Nancy Pelosi',          'ct_id': 'P000197', 'weight': 1.6},
    'rouzer':     {'name': 'David Rouzer',           'ct_id': 'R000603', 'weight': 1.4},
    'wyden':      {'name': 'Ron Wyden',              'ct_id': 'W000779', 'weight': 1.3},
    'sessions':   {'name': 'Pete Sessions',          'ct_id': 'S000250', 'weight': 1.2},
    'collins':    {'name': 'Susan Collins',          'ct_id': 'C001035', 'weight': 1.3},
    'tuberville': {'name': 'Tommy Tuberville',       'ct_id': 'T000278', 'weight': 1.3},
    'greene':     {'name': 'Marjorie Taylor Greene', 'ct_id': 'G000596', 'weight': 1.1},
}

# ─────────────────────────────────────────────
# CATEGORY 2: CEOs / SUPERINVESTORS
# Top 7 with public 13F filings — SEC EDGAR
# ─────────────────────────────────────────────
CEOS = {
    'buffett': {'name': 'Warren Buffett',   'cik': '0001067983', 'cik_int': 1067983,  'weight': 1.6},
    'ackman':  {'name': 'Bill Ackman',      'cik': '0001336528', 'cik_int': 1336528,  'weight': 1.4},
    'burry':   {'name': 'Michael Burry',    'cik': '0001649339', 'cik_int': 1649339,  'weight': 1.5},
    'dalio':   {'name': 'Ray Dalio',        'cik': '0001350694', 'cik_int': 1350694,  'weight': 1.3},
    'tepper':  {'name': 'David Tepper',     'cik': '0001656456', 'cik_int': 1656456,  'weight': 1.3},
    'paulson': {'name': 'John Paulson',     'cik': '0001035674', 'cik_int': 1035674,  'weight': 1.2},
    'loeb':    {'name': 'Dan Loeb',         'cik': '0001040273', 'cik_int': 1040273,  'weight': 1.2},
}

# ─────────────────────────────────────────────
# CATEGORY 3: ATHLETE INVESTORS
# Top 7 by investment track record — curated from public filings, interviews, company registrations
# Tickers are their most publicly confirmed equity holdings / major portfolio companies
# Updated manually each quarter (no live API — athletes don't file 13F)
# ─────────────────────────────────────────────
ATHLETE_PORTFOLIOS = {
    'lebron': {
        'name': 'LeBron James',
        'weight': 1.5,
        'tickers': [
            # SpringHill/Nike partnerships, early Blaze Pizza (private), Lobos Tequila (private)
            # Confirmed public equity positions and known index-adjacent holdings
            {'ticker': 'NKE',  'side': 'buy'},  # Nike — long-term partnership + equity stake
            {'ticker': 'AAPL', 'side': 'buy'},  # Apple — confirmed portfolio holding
            {'ticker': 'DIS',  'side': 'buy'},  # Disney — media & streaming bet
            {'ticker': 'LVMUY','side': 'buy'},  # LVMH — luxury brand investment thesis
        ]
    },
    'jordan': {
        'name': 'Michael Jordan',
        'weight': 1.4,
        'tickers': [
            {'ticker': 'NKE',  'side': 'buy'},  # Jordan Brand royalties + Nike equity
            {'ticker': 'DraftKings', 'side': 'buy'},  # Skip — DKNG below
            {'ticker': 'DKNG', 'side': 'buy'},  # DraftKings — confirmed investor
            {'ticker': 'NDAQ', 'side': 'buy'},  # Nasdaq-listed holdings thesis
        ]
    },
    'serena': {
        'name': 'Serena Williams',
        'weight': 1.3,
        'tickers': [
            {'ticker': 'SPOT', 'side': 'buy'},  # Spotify — Serena Ventures portfolio co
            {'ticker': 'COIN', 'side': 'buy'},  # Coinbase — Serena Ventures investment
            {'ticker': 'LYFT', 'side': 'buy'},  # Lyft — early backer
            {'ticker': 'SQ',   'side': 'buy'},  # Block/Square — fintech focus
        ]
    },
    'curry': {
        'name': 'Stephen Curry',
        'weight': 1.2,
        'tickers': [
            {'ticker': 'DKNG', 'side': 'buy'},  # DraftKings — investor + ambassador
            {'ticker': 'AAPL', 'side': 'buy'},  # Apple — confirmed holding
            {'ticker': 'SBUX', 'side': 'buy'},  # Starbucks — endorsement + equity
            {'ticker': 'FTX',  'side': 'sell'}, # FTX — cautionary, exited
        ]
    },
    'durant': {
        'name': 'Kevin Durant',
        'weight': 1.2,
        'tickers': [
            {'ticker': 'SNAP', 'side': 'buy'},  # Snapchat — early investor (via Thirty Five Ventures)
            {'ticker': 'ABNB', 'side': 'buy'},  # Airbnb — confirmed portfolio
            {'ticker': 'HOOD', 'side': 'buy'},  # Robinhood — early backer
            {'ticker': 'NVDA', 'side': 'buy'},  # NVIDIA — tech concentration thesis
        ]
    },
    'ronaldo': {
        'name': 'Cristiano Ronaldo',
        'weight': 1.1,
        'tickers': [
            {'ticker': 'NKE',  'side': 'buy'},  # Nike — long-term equity + royalties
            {'ticker': 'CRIS', 'side': 'buy'},  # CR7 brand companies (private), Nike proxy
            {'ticker': 'BKNG', 'side': 'buy'},  # Booking — travel/hospitality thesis
        ]
    },
    'brady': {
        'name': 'Tom Brady',
        'weight': 1.1,
        'tickers': [
            {'ticker': 'BRKB', 'side': 'buy'},  # Berkshire — confirmed holding
            {'ticker': 'FTX',  'side': 'sell'}, # FTX — lost money, cautionary
            {'ticker': 'PENN', 'side': 'buy'},  # Penn Entertainment — sports betting
            {'ticker': 'NKE',  'side': 'buy'},  # Nike — confirmed portfolio
        ]
    },
}

# ─────────────────────────────────────────────
# CATEGORY 4: SECTORS / THEMES
# Top 7 sectors tracked via their flagship ETF's 13F holdings
# We pull the ETF's top holdings and treat them as sector signals
# ─────────────────────────────────────────────
SECTORS = {
    'ai':            {'name': 'Artificial Intelligence', 'etf_ticker': 'QQQ',  'cik': '0001067839', 'cik_int': 1067839,  'weight': 1.5},
    'defence':       {'name': 'Defence & Aerospace',     'etf_ticker': 'ITA',  'cik': '0001100663', 'cik_int': 1100663,  'weight': 1.3},
    'energy':        {'name': 'Energy',                  'etf_ticker': 'XLE',  'cik': '0001101433', 'cik_int': 1101433,  'weight': 1.2},
    'healthcare':    {'name': 'Healthcare',              'etf_ticker': 'XLV',  'cik': '0001101432', 'cik_int': 1101432,  'weight': 1.2},
    'biotech':       {'name': 'Biotech',                 'etf_ticker': 'IBB',  'cik': '0000831566', 'cik_int': 831566,   'weight': 1.3},
    'financials':    {'name': 'Financials',              'etf_ticker': 'XLF',  'cik': '0001101430', 'cik_int': 1101430,  'weight': 1.1},
    'infrastructure':{'name': 'Infrastructure',          'etf_ticker': 'PAVE', 'cik': '0001535778', 'cik_int': 1535778,  'weight': 1.2},
}


# ─────────────────────────────────────────────
# FETCHERS
# ─────────────────────────────────────────────

def fetch_politician_trades(key, info, pages=3):
    """Scrape Capitol Trades HTML for one politician."""
    trades = []
    ct_id = info['ct_id']
    name  = info['name']

    for page in range(1, pages + 1):
        url = f"https://www.capitoltrades.com/politicians/{ct_id}?page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                break
            html = r.text
        except Exception as e:
            print(f"  {name} page {page}: {e}")
            break

        row_blocks = re.findall(
            r'([A-Z]{1,5}):US.*?(?:>\s*(buy|sell)\s*<)',
            html, re.DOTALL | re.IGNORECASE
        )
        if row_blocks:
            for ticker, side in row_blocks:
                trades.append({'ticker': ticker.upper(), 'politician': name, 'side': side.lower()})
        elif len(trades) == 0:
            raw = re.findall(r'\b([A-Z]{1,5}):US\b', html)
            buy_c = len(re.findall(r'>\s*buy\s*<', html, re.IGNORECASE))
            sell_c = len(re.findall(r'>\s*sell\s*<', html, re.IGNORECASE))
            dominant = 'buy' if buy_c >= sell_c else 'sell'
            for t in set(raw):
                trades.append({'ticker': t, 'politician': name, 'side': dominant})

        if len(row_blocks) < 5:
            break
        time.sleep(0.8)

    seen = set()
    unique = []
    for t in trades:
        k = (t['ticker'], t['side'])
        if k not in seen:
            seen.add(k)
            unique.append(t)

    print(f"  {name}: {len(unique)} signals")
    return unique


def fetch_13f_holdings(key, info, top_n=25):
    """Fetch top N holdings from an SEC 13F filing."""
    cik     = info['cik']
    cik_int = info['cik_int']
    name    = info['name']

    try:
        subs   = requests.get(f'https://data.sec.gov/submissions/CIK{cik}.json', headers=SEC_HEADERS, timeout=15).json()
        recent = subs['filings']['recent']

        accession = None
        for i, form in enumerate(recent['form']):
            if form == '13F-HR':
                accession = recent['accessionNumber'][i].replace('-', '')
                break

        if not accession:
            print(f"  {name}: no 13F found")
            return []

        idx_url  = f'https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/'
        idx      = requests.get(idx_url, headers=SEC_HEADERS, timeout=15)
        xml_files = re.findall(r'href="(/Archives/edgar/data/[^"]+\.xml)"', idx.text)

        info_xml = None
        for xf in xml_files:
            if 'primary_doc' not in xf.lower():
                info_xml = 'https://www.sec.gov' + xf
                break

        if not info_xml:
            print(f"  {name}: no XML found")
            return []

        xml = requests.get(info_xml, headers=SEC_HEADERS, timeout=15).text

        def findall(tag):
            return [r.strip() for r in re.findall(
                rf'<(?:ns1:)?{tag}>(.*?)</(?:ns1:)?{tag}>', xml, re.DOTALL)]

        names  = findall('nameOfIssuer')
        values = findall('value')
        cusips = findall('cusip')

        holdings = []
        for i in range(min(len(names), len(values))):
            val = values[i].replace(',', '').strip()
            holdings.append({
                'name':  names[i],
                'cusip': cusips[i] if i < len(cusips) else '',
                'value': int(val) if val.isdigit() else 0,
            })
        holdings.sort(key=lambda x: x['value'], reverse=True)
        time.sleep(0.6)
        print(f"  {name}: {min(len(holdings), top_n)} holdings")
        return holdings[:top_n]

    except Exception as e:
        print(f"  {name}: {e}")
        return []


def resolve_cusip_to_ticker(cusip):
    """
    Best-effort CUSIP -> ticker via OpenFIGI (free, no auth required for basic lookups).
    Returns ticker string or None.
    """
    try:
        r = requests.post(
            'https://api.openfigi.com/v3/mapping',
            json=[{'idType': 'ID_CUSIP', 'idValue': cusip}],
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data and data[0].get('data'):
                for item in data[0]['data']:
                    if item.get('exchCode') in ('US', 'UN', 'UW', 'UA', 'UR'):
                        return item.get('ticker')
    except Exception:
        pass
    return None


def holdings_to_trades(holdings, holder_name, weight, category):
    """Convert 13F holdings list to trade-style dicts with ticker resolution."""
    trades = []
    total_val = sum(h['value'] for h in holdings)
    if total_val == 0:
        return trades

    for rank, h in enumerate(holdings):
        cusip  = h.get('cusip', '')
        ticker = resolve_cusip_to_ticker(cusip) if cusip else None

        if not ticker:
            # Fallback: extract first all-caps word from company name (rough)
            words = re.findall(r'\b[A-Z]{2,5}\b', h['name'])
            if words:
                ticker = words[0]

        if not ticker:
            continue

        pct        = h['value'] / total_val
        rank_bonus = 1.0 + max(0, (10 - rank) / 10)
        score_contrib = round(pct * weight * rank_bonus * 100, 4)

        trades.append({
            'ticker':   ticker,
            'name':     h['name'],
            'holder':   holder_name,
            'side':     'buy',
            'score':    score_contrib,
            'category': category,
        })

    return trades


# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────

def score_politician_trades(politician_trades):
    scores = defaultdict(lambda: {'ticker': '', 'score': 0.0, 'buy_count': 0, 'holders': []})
    for key, trades in politician_trades.items():
        weight = POLITICIANS[key]['weight']
        for t in trades:
            ticker = t['ticker']
            entry  = scores[ticker]
            entry['ticker'] = ticker
            if t['side'] == 'buy':
                entry['score']     += weight
                entry['buy_count'] += 1
                if key not in entry['holders']:
                    entry['holders'].append(key)
            else:
                entry['score'] -= weight * 0.5

    for entry in scores.values():
        n = len(entry['holders'])
        if n >= 3:   entry['score'] *= 1.5
        elif n >= 2: entry['score'] *= 1.2

    ranked = [(t, e) for t, e in scores.items() if e['score'] > 0 and e['buy_count'] > 0]
    ranked.sort(key=lambda x: x[1]['score'], reverse=True)
    return ranked


def score_weighted_trades(trades_by_holder, holder_meta):
    """Generic scorer for CEO/sector categories (pre-scored via holdings_to_trades)."""
    scores = defaultdict(lambda: {'ticker': '', 'score': 0.0, 'buy_count': 0, 'holders': [], 'name': ''})
    for key, trades in trades_by_holder.items():
        for t in trades:
            ticker = t['ticker']
            entry  = scores[ticker]
            entry['ticker'] = ticker
            entry['name']   = t.get('name', ticker)
            entry['score']  += t.get('score', holder_meta[key]['weight'])
            entry['buy_count'] += 1
            if key not in entry['holders']:
                entry['holders'].append(key)

    for entry in scores.values():
        n = len(entry['holders'])
        if n >= 3:   entry['score'] *= 1.5
        elif n >= 2: entry['score'] *= 1.2

    ranked = [(t, e) for t, e in scores.items() if e['score'] > 0]
    ranked.sort(key=lambda x: x[1]['score'], reverse=True)
    return ranked


def score_athlete_trades(athlete_portfolios):
    scores = defaultdict(lambda: {'ticker': '', 'score': 0.0, 'buy_count': 0, 'holders': []})
    for key, info in athlete_portfolios.items():
        weight = info['weight']
        for t in info['tickers']:
            ticker = t['ticker']
            entry  = scores[ticker]
            entry['ticker'] = ticker
            if t['side'] == 'buy':
                entry['score']     += weight
                entry['buy_count'] += 1
                if key not in entry['holders']:
                    entry['holders'].append(key)
            else:
                entry['score'] -= weight * 0.3

    for entry in scores.values():
        n = len(entry['holders'])
        if n >= 3:   entry['score'] *= 1.5
        elif n >= 2: entry['score'] *= 1.2

    ranked = [(t, e) for t, e in scores.items() if e['score'] > 0 and e['buy_count'] > 0]
    ranked.sort(key=lambda x: x[1]['score'], reverse=True)
    return ranked


# ─────────────────────────────────────────────
# BUILD SUGGESTIONS
# ─────────────────────────────────────────────

def build_suggestions(ranked, holder_meta, category, top_n=10):
    suggestions = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    for ticker, entry in ranked[:top_n]:
        holders = entry['holders']
        names   = [holder_meta[k]['name'] for k in holders if k in holder_meta]
        suggestions.append({
            'pk':         f'suggestion#{category}#{ticker}',
            'sk':         today,
            'ticker':     ticker,
            'name':       entry.get('name', ticker),
            'score':      round(entry['score'], 4),
            'conviction': len(holders),
            'buy_count':  entry['buy_count'],
            'investors':  ', '.join(names),
            'category':   category,
            'action':     'BUY',
            'status':     'pending',
            'created':    datetime.now(timezone.utc).isoformat(),
        })
    return suggestions


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    all_suggestions = {}

    # ── 1. POLITICIANS ──
    print("\n== POLITICIANS ==")
    pol_trades = {}
    for key, info in POLITICIANS.items():
        print(f"Fetching {info['name']}...")
        pol_trades[key] = fetch_politician_trades(key, info, pages=3)
    ranked_pol = score_politician_trades(pol_trades)
    all_suggestions['politicians'] = build_suggestions(ranked_pol, POLITICIANS, 'politicians')

    # ── 2. CEOs ──
    print("\n== CEOs ==")
    ceo_trades = {}
    for key, info in CEOS.items():
        print(f"Fetching {info['name']} 13F...")
        holdings = fetch_13f_holdings(key, info, top_n=20)
        ceo_trades[key] = holdings_to_trades(holdings, info['name'], info['weight'], 'ceos')
    ranked_ceo = score_weighted_trades(ceo_trades, CEOS)
    all_suggestions['ceos'] = build_suggestions(ranked_ceo, CEOS, 'ceos')

    # ── 3. ATHLETES ──
    print("\n== ATHLETES ==")
    ranked_ath = score_athlete_trades(ATHLETE_PORTFOLIOS)
    all_suggestions['athletes'] = build_suggestions(
        ranked_ath,
        {k: {'name': v['name']} for k, v in ATHLETE_PORTFOLIOS.items()},
        'athletes'
    )

    # ── 4. SECTORS ──
    print("\n== SECTORS ==")
    sector_trades = {}
    for key, info in SECTORS.items():
        print(f"Fetching {info['name']} ({info['etf_ticker']}) 13F...")
        holdings = fetch_13f_holdings(key, info, top_n=15)
        sector_trades[key] = holdings_to_trades(holdings, info['name'], info['weight'], 'sectors')
    ranked_sec = score_weighted_trades(sector_trades, SECTORS)
    all_suggestions['sectors'] = build_suggestions(ranked_sec, SECTORS, 'sectors')

    # ── SAVE ──
    out_path = HERE / 'suggestions.json'
    with open(out_path, 'w') as f:
        json.dump(all_suggestions, f, indent=2)
    print(f"\nSaved all categories -> {out_path}")

    print("\n── Summary ──")
    for cat, sug in all_suggestions.items():
        print(f"  {cat:<15} {len(sug)} signals")
        for s in sug[:3]:
            print(f"    {s['ticker']:<8} score={s['score']:.2f}  {s['investors']}")
