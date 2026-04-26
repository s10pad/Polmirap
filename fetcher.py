import requests
import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

HEADERS = {'User-Agent': 'MirrorAI arnaudpkengni@gmail.com'}

HERE = Path(__file__).parent

# Top 7 US politicians ranked by portfolio returns and trading volume (Unusual Whales 2024 report)
# Capitol Trades IDs match the standard bioguide format
POLITICIANS = {
    'pelosi':   {'name': 'Nancy Pelosi',         'ct_id': 'P000197'},
    'tuberville':{'name': 'Tommy Tuberville',     'ct_id': 'T000278'},
    'collins':  {'name': 'Susan Collins',         'ct_id': 'C001035'},
    'rouzer':   {'name': 'David Rouzer',          'ct_id': 'R000603'},
    'wyden':    {'name': 'Ron Wyden',             'ct_id': 'W000779'},
    'sessions': {'name': 'Pete Sessions',         'ct_id': 'S000250'},
    'greene':   {'name': 'Marjorie Taylor Greene', 'ct_id': 'G000596'},
}

# Weights based on track record — Pelosi is the standout, others are competitive
POLITICIAN_WEIGHTS = {
    'pelosi':    1.6,
    'tuberville': 1.3,
    'collins':   1.3,
    'rouzer':    1.4,
    'wyden':     1.3,
    'sessions':  1.2,
    'greene':    1.1,
}

# Public S3 datasets maintained by community watchers (STOCK Act disclosures)
HOUSE_URL  = 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json'
SENATE_URL = 'https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json'


def fetch_all_congressional_trades():
    """Pull the full House + Senate trade disclosure datasets."""
    print("Fetching House disclosures...")
    try:
        house = requests.get(HOUSE_URL, headers=HEADERS, timeout=30).json()
        print(f"  {len(house)} House records")
    except Exception as e:
        print(f"  House fetch failed: {e}")
        house = []

    print("Fetching Senate disclosures...")
    try:
        senate = requests.get(SENATE_URL, headers=HEADERS, timeout=30).json()
        print(f"  {len(senate)} Senate records")
    except Exception as e:
        print(f"  Senate fetch failed: {e}")
        senate = []

    return house + senate


def filter_by_politicians(all_trades):
    """
    Filter the raw trades down to our 7 target politicians.
    Returns a dict keyed by politician slug with list of their trades.
    """
    results = {key: [] for key in POLITICIANS}

    for t in all_trades:
        rep_name = t.get('representative', t.get('senator', ''))
        for key, info in POLITICIANS.items():
            last_name = info['name'].split()[-1]
            if last_name.lower() in rep_name.lower():
                ticker = t.get('ticker', '')
                if not ticker or ticker == '--':
                    continue
                trade_type = t.get('type', t.get('transaction_type', '')).lower()
                # Normalise to buy / sell
                if 'purchase' in trade_type or 'buy' in trade_type:
                    side = 'buy'
                elif 'sale' in trade_type or 'sell' in trade_type:
                    side = 'sell'
                else:
                    continue
                results[key].append({
                    'ticker':      ticker.upper().strip(),
                    'politician':  info['name'],
                    'side':        side,
                    'amount':      t.get('amount', '$1,001 - $15,000'),
                    'date':        t.get('transaction_date', t.get('date', '')),
                    'filing_date': t.get('disclosure_date', t.get('filed', '')),
                    'type':        t.get('asset_type', 'stock'),
                })
                break

    for key, trades in results.items():
        print(f"  {POLITICIANS[key]['name']}: {len(trades)} trades found")

    return results


def score_trades(politician_trades):
    """
    Score each ticker across all 7 politicians.
    Buys add score, sells subtract. Weighted by politician track record.
    Returns a sorted list of (ticker, score_data) tuples.
    """
    from collections import defaultdict
    scores = defaultdict(lambda: {
        'ticker': '',
        'score': 0.0,
        'buy_count': 0,
        'sell_count': 0,
        'politicians': [],
        'total_amount_k': 0,
    })

    for key, trades in politician_trades.items():
        weight = POLITICIAN_WEIGHTS.get(key, 1.0)
        # count buys per ticker for this politician
        ticker_buys  = Counter(t['ticker'] for t in trades if t['side'] == 'buy')
        ticker_sells = Counter(t['ticker'] for t in trades if t['side'] == 'sell')
        all_tickers  = set(ticker_buys) | set(ticker_sells)

        for ticker in all_tickers:
            buys  = ticker_buys.get(ticker, 0)
            sells = ticker_sells.get(ticker, 0)
            net   = buys - sells
            if net <= 0:
                continue  # only surface net-buy positions

            entry = scores[ticker]
            entry['ticker'] = ticker
            entry['score']     += net * weight
            entry['buy_count'] += buys
            if key not in entry['politicians']:
                entry['politicians'].append(key)

    # Conviction multiplier for stocks bought by multiple politicians
    for ticker, entry in scores.items():
        n = len(entry['politicians'])
        if n >= 3:
            entry['score'] *= 1.5
        elif n >= 2:
            entry['score'] *= 1.2

    ranked = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    return ranked


def build_suggestions(ranked, politician_trades, top_n=10):
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
    all_trades = fetch_all_congressional_trades()

    print("\nFiltering for target politicians...")
    politician_trades = filter_by_politicians(all_trades)

    print("\nScoring tickers...")
    ranked = score_trades(politician_trades)

    suggestions = build_suggestions(ranked, politician_trades, top_n=10)

    print(f"\nTop {len(suggestions)} signals:")
    print(f"{'Rank':<5} {'Ticker':<10} {'Score':>8} {'Conviction':>10}  Investors")
    print('-' * 70)
    for i, s in enumerate(suggestions, 1):
        print(f"{i:<5} {s['ticker']:<10} {s['score']:>8.2f} {s['conviction']:>10}  {s['investors']}")

    out_path = HERE / 'suggestions.json'
    with open(out_path, 'w') as f:
        json.dump(suggestions, f, indent=2)
    print(f"\nSaved {len(suggestions)} suggestions to {out_path}")

    raw_path = HERE / 'politician_trades.json'
    with open(raw_path, 'w') as f:
        json.dump(politician_trades, f, indent=2)
    print(f"Saved raw trades to {raw_path}")
