"""
scorer.py — standalone re-scorer if you want to re-rank without re-fetching.
Reads politician_trades.json and rewrites suggestions.json.
"""
import json
from pathlib import Path
from fetcher import score_trades, build_suggestions, POLITICIANS

HERE = Path(__file__).parent


def main():
    raw_path = HERE / 'politician_trades.json'
    if not raw_path.exists():
        print(f"No data at {raw_path}. Run fetcher.py first.")
        return

    with open(raw_path) as f:
        politician_trades = json.load(f)

    for key, trades in politician_trades.items():
        print(f"  {POLITICIANS.get(key, {}).get('name', key)}: {len(trades)} trades")

    print("\nScoring...")
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
    print(f"\nSaved to {out_path}")


if __name__ == '__main__':
    main()
