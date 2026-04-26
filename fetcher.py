import requests
import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

HERE = Path(__file__).parent

# Top 7 US politicians ranked by portfolio returns — Unusual Whales 2024 report
# Capitol Trades bioguide IDs (standard congressional identifiers)
POLITICIANS = {
    'pelosi':    {'name': 'Nancy Pelosi',          'ct_id': 'P000197', 'weight': 1.6},
    'rouzer':    {'name': 'David Rouzer',           'ct_id': 'R000603', 'weight': 1.4},
    'wyden':     {'name': 'Ron Wyden',              'ct_id': 'W000779', 'weight': 1.3},
    'sessions':  {'name': 'Pete Sessions',          'ct_id': 'S000250', 'weight': 1.2},
    'collins':   {'name': 'Susan Collins',          'ct_id': 'C001035', 'weight': 1.3},
    'tuberville':{'name': 'Tommy Tuberville',       'ct_id': 'T000278', 'weight': 1.3},
    'greene':    {'name': 'Marjorie Taylor Greene', 'ct_id': 'G000596', 'weight': 1.1},
}

CT_BASE = 'https://www.capitoltrades.com'


def fetch_politician_trades(key, info, pages=3):
    """
    Scrape Capitol Trades HTML for one politician.
    Extracts ticker symbols and buy/sell type from the rendered trade table.
    Returns a list of trade dicts.
    """
    trades = []
    ct_id = info['ct_id']
    name  = info['name']

    for page in range(1, pages + 1):
        url = f"{CT_BASE}/politicians/{ct_id}?page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                print(f"  {name} page {page}: HTTP {r.status_code}")
                break
            html = r.text
        except Exception as e:
            print(f"  {name} page {page}: {e}")
            break

        # Extract tickers — appear as "TICKER:US" in the HTML
        raw_tickers = re.findall(r'\b([A-Z]{1,5}):US\b', html)

        # Extract trade types — "buy" or "sell" class markers in the trade rows
        buy_cells  = len(re.findall(r'>\s*buy\s*<', html, re.IGNORECASE))
        sell_cells = len(re.findall(r'>\s*sell\s*<', html, re.IGNORECASE))

        # Extract trade dates (ISO format yyyy-mm-dd or similar)
        dates = re.findall(r'\b(202[3-9]-\d{2}-\d{2})\b', html)

        # Extract dollar amounts e.g. "15K–50K", "1K–15K", "50K–100K"
        amounts = re.findall(r'(\d+K)[\u2013\-]+(\d+K)', html)

        # Build per-ticker side mapping: pair tickers to buy/sell by DOM order.
        # The page lists N rows; each row has exactly one ticker and one side.
        # We parse them together by finding the repeating block pattern.
        row_blocks = re.findall(
            r'([A-Z]{1,5}):US.*?(?:>\s*(buy|sell)\s*<)',
            html, re.DOTALL | re.IGNORECASE
        )

        if row_blocks:
            for ticker, side in row_blocks:
                trades.append({
                    'ticker':     ticker.upper(),
                    'politician': name,
                    'side':       side.lower(),
                    'source':     'capitoltrades',
                })
        elif raw_tickers:
            # Fallback: can't pair side to ticker — assign all as buys if more buys than sells
            dominant = 'buy' if buy_cells >= sell_cells else 'sell'
            for ticker in set(raw_tickers):
                trades.append({
                    'ticker':     ticker.upper(),
                    'politician': name,
                    'side':       dominant,
                    'source':     'capitoltrades_fallback',
                })

        # Stop if we got fewer rows than expected (last page)
        if len(row_blocks) < 5 and len(raw_tickers) < 5:
            break

        time.sleep(0.8)  # be polite

    # Deduplicate (same ticker+side may appear multiple times across pages)
    seen = set()
    unique = []
    for t in trades:
        k = (t['ticker'], t['side'])
        if k not in seen:
            seen.add(k)
            unique.append(t)

    print(f"  {name}: {len(unique)} unique ticker+side pairs ({len(trades)} raw rows)")
    return unique


def score_trades(politician_trades):
    """
    Score each ticker across all 7 politicians.
    Buys add score * weight, sells subtract. Returns sorted list.
    """
    scores = defaultdict(lambda: {
        'ticker': '', 'score': 0.0,
        'buy_count': 0, 'sell_count': 0, 'politicians': [],
    })

    for key, trades in politician_trades.items():
        weight = POLITICIANS[key]['weight']
        for t in trades:
            ticker = t['ticker']
            side   = t['side']
            entry  = scores[ticker]
            entry['ticker'] = ticker
            if side == 'buy':
                entry['score']     += weight
                entry['buy_count'] += 1
                if key not in entry['politicians']:
                    entry['politicians'].append(key)
            elif side == 'sell':
                entry['score']     -= weight * 0.5  # sells reduce score but less aggressively
                entry['sell_count'] += 1

    # Conviction multiplier — bought by multiple politicians
    for ticker, entry in scores.items():
        n = len(entry['politicians'])
        if n >= 3:
            entry['score'] *= 1.5
        elif n >= 2:
            entry['score'] *= 1.2

    # Keep only net-buy positions
    ranked = [(t, e) for t, e in scores.items() if e['score'] > 0 and e['buy_count'] > 0]
    ranked.sort(key=lambda x: x[1]['score'], reverse=True)
    return ranked


def build_suggestions(ranked, top_n=10):
    suggestions = []
    for ticker, entry in ranked[:top_n]:
        pol_names = [POLITICIANS[k]['name'] for k in entry['politicians'] if k in POLITICIANS]
        suggestions.append({
            'pk':         f'suggestion#{ticker}',
            'sk':         datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'ticker':     ticker,
            'name':       ticker,
            'score':      round(entry['score'], 4),
            'conviction': len(entry['politicians']),
            'buy_count':  entry['buy_count'],
            'investors':  ', '.join(pol_names),
            'action':     'BUY',
            'status':     'pending',
            'created':    datetime.now(timezone.utc).isoformat(),
        })
    return suggestions


if __name__ == '__main__':
    politician_trades = {}

    for key, info in POLITICIANS.items():
        print(f"\nFetching {info['name']}...")
        politician_trades[key] = fetch_politician_trades(key, info, pages=3)

    print(f"\n{'='*50}")
    print("Scoring tickers...")
    ranked = score_trades(politician_trades)
    suggestions = build_suggestions(ranked, top_n=10)

    print(f"\nTop {len(suggestions)} signals:")
    print(f"{'Rank':<5} {'Ticker':<10} {'Score':>8} {'Conviction':>10}  {'Buys':>5}  Investors")
    print('-' * 75)
    for i, s in enumerate(suggestions, 1):
        print(f"{i:<5} {s['ticker']:<10} {s['score']:>8.2f} {s['conviction']:>10}  {s['buy_count']:>5}  {s['investors']}")

    out_path = HERE / 'suggestions.json'
    with open(out_path, 'w') as f:
        json.dump(suggestions, f, indent=2)
    print(f"\nSaved {len(suggestions)} suggestions -> {out_path}")

    raw_path = HERE / 'politician_trades.json'
    with open(raw_path, 'w') as f:
        json.dump(politician_trades, f, indent=2)
    print(f"Saved raw trades -> {raw_path}")
