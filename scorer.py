
import json
import boto3
import os
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

INVESTOR_WEIGHTS = {
    'buffett': 1.5,
    'ackman':  1.3,
    'burry':   1.4,
    'dalio':   1.2,
    'wood':    1.1,
    'pelosi':  1.0,
    'musk':    1.0,
}

def normalize_name(name):
    stopwords = ['INC', 'CORP', 'LTD', 'LLC', 'CO', 'THE', 'CLASS', 'CL', 'COM',
                 'COMMON', 'STOCK', 'SHS', 'ETF', 'FUND', 'TRUST', 'GROUP']
    words = name.upper().split()
    return ' '.join(w for w in words if w not in stopwords).strip()

def load_holdings():
    with open('/home/ubuntu/holdings.json') as f:
        return json.load(f)

def score_holdings(data):
    stock_scores = defaultdict(lambda: {
        'name': '',
        'score': 0.0,
        'investors': [],
        'total_value': 0,
        'conviction': 0,
    })

    for investor, holdings in data.items():
        if not holdings:
            continue
        weight = INVESTOR_WEIGHTS.get(investor, 1.0)

        # get total portfolio value for this investor
        total_val = sum(h.get('value', 0) for h in holdings if isinstance(h, dict))
        if total_val == 0:
            continue

        for rank, holding in enumerate(holdings):
            if not isinstance(holding, dict):
                continue
            name = holding.get('name', '')
            if not name:
                continue

            key = normalize_name(name)
            val  = holding.get('value', 0)
            if val == 0:
                continue

            # position size as % of portfolio
            pct = val / total_val if total_val > 0 else 0

            # rank bonus: top holdings get more weight
            rank_bonus = 1.0 + max(0, (10 - rank) / 10)

            contribution = pct * weight * rank_bonus * 100

            entry = stock_scores[key]
            entry['name']        = name
            entry['score']       += contribution
            entry['total_value'] += val
            entry['conviction']  += 1
            if investor not in entry['investors']:
                entry['investors'].append(investor)

    # boost stocks held by multiple investors
    for key, entry in stock_scores.items():
        n = entry['conviction']
        if n >= 3:
            entry['score'] *= 1.5
        elif n >= 2:
            entry['score'] *= 1.2

    ranked = sorted(stock_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    return ranked


def build_suggestions(ranked, top_n=10):
    suggestions = []
    for key, entry in ranked[:top_n]:
        investors_str = ', '.join(entry['investors'])
        suggestions.append({
            'pk':            f"suggestion#{key.replace(' ', '_')}",
            'sk':            datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'name':          entry['name'],
            'score':         Decimal(str(round(entry['score'], 4))),
            'conviction':    entry['conviction'],
            'investors':     investors_str,
            'total_value_k': Decimal(str(entry['total_value'])),
            'action':        'BUY',
            'status':        'pending',
            'created':       datetime.now(timezone.utc).isoformat(),
        })
    return suggestions


def save_suggestions(suggestions):
    print("\nTop trade suggestions:")
    print(f"{'Rank':<5} {'Name':<35} {'Score':>8} {'Conviction':>10} {'Investors'}")
    print('-' * 90)
    for i, s in enumerate(suggestions, 1):
        print(f"{i:<5} {s['name']:<35} {s['score']:>8.2f} {s['conviction']:>10}     {s['investors']}")

    # save locally
    with open('/home/ubuntu/suggestions.json', 'w') as f:
        class DecimalEncoder(json.JSONEncoder):
            def default(self, o):
                from decimal import Decimal
                return float(o) if isinstance(o, Decimal) else super().default(o)
        json.dump(suggestions, f, indent=2, cls=DecimalEncoder)
    print(f"\nSaved {len(suggestions)} suggestions to suggestions.json")

    # try DynamoDB
    try:
        dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        table = dynamodb.Table(os.getenv('DYNAMODB_TABLE', 'mirror-trades'))
        for s in suggestions:
            table.put_item(Item=s)
        print(f"Saved to DynamoDB")
    except Exception as e:
        print(f"DynamoDB not configured yet: {e}")


if __name__ == '__main__':
    print("Loading holdings...")
    data = load_holdings()
    for k, v in data.items():
        print(f"  {k}: {len(v)} holdings")

    print("\nScoring...")
    ranked = score_holdings(data)

    suggestions = build_suggestions(ranked, top_n=10)
    save_suggestions(suggestions)
PYEOF

python3 /home/ubuntu/scorer.py
