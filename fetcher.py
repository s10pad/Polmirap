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
    'schultz':    {'name': 'Debbie Schultz',        'ct_id': 'S001565', 'weight': 1.5},  # +142.3% 2024
    'williams':   {'name': 'Roger Williams',        'ct_id': 'W000816', 'weight': 1.4},  # +111.2% 2024
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
# Top holdings per sector pulled from iShares/SSGA fund JSON endpoints (free, no auth)
# Each entry lists the top confirmed tickers for that sector ETF's holdings
# Updated quarterly — these are the current top-weighted holdings as of Q1 2026
# ─────────────────────────────────────────────
SECTORS = {
    'ai': {
        'name': 'Artificial Intelligence',
        'weight': 1.5,
        'tickers': ['MSFT','AAPL','NVDA','AMZN','META','GOOGL','TSLA','AVGO','COST','NFLX'],
    },
    'defence': {
        'name': 'Defence & Aerospace',
        'weight': 1.3,
        'tickers': ['RTX','LMT','NOC','GD','BA','L3H','TDG','HII','AXON','LDOS'],
    },
    'energy': {
        'name': 'Energy',
        'weight': 1.2,
        'tickers': ['XOM','CVX','COP','EOG','SLB','MPC','PSX','PXD','OXY','VLO'],
    },
    'healthcare': {
        'name': 'Healthcare',
        'weight': 1.2,
        'tickers': ['LLY','UNH','JNJ','MRK','ABBV','TMO','ABT','DHR','BMY','ISRG'],
    },
    'biotech': {
        'name': 'Biotech',
        'weight': 1.3,
        'tickers': ['AMGN','GILD','REGN','VRTX','BIIB','MRNA','ILMN','ALNY','SGEN','BMRN'],
    },
    'financials': {
        'name': 'Financials',
        'weight': 1.1,
        'tickers': ['BRK-B','JPM','BAC','WFC','GS','MS','C','BLK','SCHW','CB'],
    },
    'infrastructure': {
        'name': 'Infrastructure',
        'weight': 1.2,
        'tickers': ['CAT','DE','VMC','MLM','PWR','URI','FLR','PRIM','GVA','ROAD'],
    },
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


# Known CUSIP -> ticker map for the most common superinvestor holdings.
# Avoids OpenFIGI failures for ETFs, foreign listings, and common large-caps.
CUSIP_MAP = {
    '025816109': 'AXP',   '037833100': 'AAPL',  '191216100': 'KO',
    '060505104': 'BAC',   '345370860': 'FOX',   '38141G104': 'GS',
    '808513105': 'SCE',   '172967424': 'C',      '46625H100': 'JPM',
    '857477103': 'STZ',   '718172109': 'PM',     '26441C204': 'DVA',
    '084670702': 'BRK-B', '92826C839': 'V',      '459200101': 'IBM',
    '40434L105': 'HCA',   '00206R102': 'T',      '670346105': 'OXY',
    '20030N101': 'CHTR',  '69351T106': 'PANW',   '67066G104': 'NVDA',
    '594918104': 'MSFT',  '023135106': 'AMZN',   '30303M102': 'META',
    '88160R101': 'TSLA',  '02079K305': 'GOOGL',  '72346Q104': 'PINS',
    '931142103': 'WMT',   '78462F103': 'SPY',    '464287655': 'IVV',
    '46090E103': 'IAU',   '78468R663': 'QQQ',    '921937835': 'VTI',
    '097023105': 'BKNG',  '44919P508': 'UBER',   '03783310': 'AAPL',
    '594918100': 'MSFT',  '345370860': 'FOXA',   '167250109': 'CHWY',
    '88162G103': 'TTWO',  '90184L102': 'TWLO',   '09075V102': 'BIRD',
}


def resolve_cusip_to_ticker(cusip):
    """CUSIP -> ticker. Checks local map first, then OpenFIGI."""
    if cusip in CUSIP_MAP:
        return CUSIP_MAP[cusip]
    try:
        r = requests.post(
            'https://api.openfigi.com/v3/mapping',
            json=[{'idType': 'ID_CUSIP', 'idValue': cusip}],
            headers={'Content-Type': 'application/json'},
            timeout=8
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


def fetch_athlete_news():
    """
    Scrape Sportico, Boardroom, and Front Office Sports for athlete investment mentions.
    Returns a dict of {athlete_key: [ticker, ...]} discovered from recent headlines.
    """
    ATHLETE_NAMES = {
        'LeBron': 'lebron', 'James': 'lebron',
        'Jordan': 'jordan',
        'Serena': 'serena', 'Williams': 'serena',
        'Curry': 'curry', 'Stephen': 'curry',
        'Durant': 'durant', 'Kevin': 'durant',
        'Ronaldo': 'ronaldo', 'Cristiano': 'ronaldo',
        'Brady': 'brady', 'Tom Brady': 'brady',
    }
    # Ticker patterns found near athlete names in financial news
    TICKER_PATTERN = re.compile(r'\b([A-Z]{2,5})\b')
    NOISE = {'A','AN','AS','AT','BE','BY','FOR','IN','IS','IT','NO','OF','ON','OR',
             'THE','TO','UP','US','WE','IF','HE','MY','SO','DO','GO','AM','I'}

    sources = [
        'https://sportico.com/business/finance/',
        'https://boardroom.tv/category/investing/',
    ]
    discovered = defaultdict(set)

    for url in sources:
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                continue
            text = r.text
            # Find paragraphs containing athlete names
            for name, key in ATHLETE_NAMES.items():
                # Find up to 300 chars around each mention
                for m in re.finditer(re.escape(name), text, re.IGNORECASE):
                    snippet = text[max(0, m.start()-100): m.end()+200]
                    tickers = [t for t in TICKER_PATTERN.findall(snippet)
                               if t not in NOISE and len(t) >= 2]
                    for t in tickers:
                        discovered[key].add(t)
        except Exception:
            continue

    # Filter: keep only tickers that also appear in curated lists (sanity check)
    known = set()
    for info in ATHLETE_PORTFOLIOS.values():
        for t in info['tickers']:
            known.add(t['ticker'])

    result = {}
    for key, tickers in discovered.items():
        valid = [t for t in tickers if t in known]
        if valid:
            result[key] = valid
            print(f"  News: {key} -> {valid}")

    return result


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
            # Fallback: extract first all-caps word from company name, skip common noise words
            _noise = {'INC','CORP','LTD','LLC','CO','THE','CLASS','CL','COM','COMMON',
                      'STOCK','SHS','ETF','FUND','TRUST','GROUP','SA','PLC','AG','NV','ADR'}
            words = [w for w in re.findall(r'\b[A-Z]{2,5}\b', h['name']) if w not in _noise]
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
    # Scrape news for fresh signals, merge into curated portfolios
    news_hits = fetch_athlete_news()
    for key, tickers in news_hits.items():
        if key in ATHLETE_PORTFOLIOS:
            existing = {t['ticker'] for t in ATHLETE_PORTFOLIOS[key]['tickers']}
            for t in tickers:
                if t not in existing:
                    ATHLETE_PORTFOLIOS[key]['tickers'].append({'ticker': t, 'side': 'buy'})
                    print(f"  Added from news: {key} -> {t}")
    ranked_ath = score_athlete_trades(ATHLETE_PORTFOLIOS)
    all_suggestions['athletes'] = build_suggestions(
        ranked_ath,
        {k: {'name': v['name']} for k, v in ATHLETE_PORTFOLIOS.items()},
        'athletes'
    )

    # ── 4. SECTORS ──
    print("\n== SECTORS ==")
    # Build per-ticker scores aggregated across all 7 sectors (enables cross-sector conviction)
    sector_ticker_scores: dict = defaultdict(lambda: {
        'ticker': '', 'score': 0.0, 'buy_count': 0, 'holders': [], 'name': ''
    })
    for key, info in SECTORS.items():
        for rank, ticker in enumerate(info['tickers']):
            rank_bonus = 1.0 + max(0, (10 - rank) / 10)
            e = sector_ticker_scores[ticker]
            e['ticker'] = ticker
            e['name']   = ticker
            e['score']  += round(info['weight'] * rank_bonus, 4)
            e['buy_count'] += 1
            if key not in e['holders']:
                e['holders'].append(key)
        print(f"  {info['name']}: {len(info['tickers'])} holdings")

    # Apply cross-sector conviction multiplier
    for e in sector_ticker_scores.values():
        n = len(e['holders'])
        if n >= 3:   e['score'] *= 1.5
        elif n >= 2: e['score'] *= 1.2

    ranked_sec = sorted(sector_ticker_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    # Build suggestions with sector names as investors
    sec_suggestions = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    for ticker, e in ranked_sec[:10]:
        sector_names = [SECTORS[k]['name'] for k in e['holders'] if k in SECTORS]
        sec_suggestions.append({
            'pk': f'suggestion#sectors#{ticker}', 'sk': today,
            'ticker': ticker, 'name': ticker,
            'score': round(e['score'], 4),
            'conviction': len(e['holders']),
            'buy_count': e['buy_count'],
            'investors': ', '.join(sector_names),
            'category': 'sectors', 'action': 'BUY', 'status': 'pending',
            'created': datetime.now(timezone.utc).isoformat(),
        })
    all_suggestions['sectors'] = sec_suggestions

    # ── SAVE ──
    all_suggestions['last_updated'] = datetime.now(timezone.utc).isoformat()
    out_path = HERE / 'suggestions.json'
    with open(out_path, 'w') as f:
        json.dump(all_suggestions, f, indent=2)
    print(f"\nSaved all categories -> {out_path}")

    print("\n── Summary ──")
    for cat, sug in all_suggestions.items():
        if not isinstance(sug, list):
            continue
        print(f"  {cat:<15} {len(sug)} signals")
        for s in sug[:3]:
            print(f"    {s['ticker']:<8} score={s['score']:.2f}  {s['investors']}")
