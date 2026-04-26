import os
import json
import requests
import boto3
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from database import DuplicateHandler
from strategy import MirrorStrategy

# Top 7 US politicians by trading returns (Unusual Whales 2024)
TARGET_POLITICIANS = [
    'Pelosi',
    'Tuberville',
    'Collins',
    'Rouzer',
    'Wyden',
    'Sessions',
    'Greene',
]

HOUSE_URL  = 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json'
SENATE_URL = 'https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json'


def lambda_handler(event, context):
    sm   = boto3.client('secretsmanager')
    resp = sm.get_secret_value(SecretId='Fintech/PoliticianTrading')
    creds = json.loads(resp['SecretString'])

    is_paper = os.getenv('DRY_RUN', 'True') == 'True'
    trading_client = TradingClient(creds['ALPACA_KEY'], creds['ALPACA_SECRET'], paper=is_paper)
    db   = DuplicateHandler()
    strat = MirrorStrategy(float(trading_client.get_account().buying_power))

    all_trades = []
    for url in [HOUSE_URL, SENATE_URL]:
        try:
            all_trades += requests.get(url, timeout=20).json()
        except Exception as e:
            print(f'Failed to fetch {url}: {e}')

    executed = 0
    for t in all_trades:
        # Only PTR (Periodic Transaction Reports) — tightest disclosure lag
        if t.get('filing_type', 'P') != 'P':
            continue

        name   = t.get('representative', t.get('senator', ''))
        ticker = t.get('ticker', '')

        if not ticker or ticker == '--':
            continue

        if not any(target.lower() in name.lower() for target in TARGET_POLITICIANS):
            continue

        trade_type = t.get('type', t.get('transaction_type', '')).lower()
        if 'purchase' in trade_type or 'buy' in trade_type:
            side = OrderSide.BUY
        elif 'sale' in trade_type or 'sell' in trade_type:
            side = OrderSide.SELL
        else:
            continue

        internal_id = f"{ticker}_{name.split()[-1]}_{t.get('transaction_date', '')}".replace('/', '')

        if db.already_processed(internal_id):
            continue

        notional = strat.calculate_notional(t.get('amount', '$1,001 - $15,000'))
        if notional < 1.0:
            continue

        try:
            order = MarketOrderRequest(
                symbol=ticker.upper(),
                notional=notional,
                side=side,
                time_in_force=TimeInForce.DAY,
            )
            trading_client.submit_order(order)
            db.mark_processed(internal_id, t)
            executed += 1
            print(f'Mirrored {name}: {side} {ticker} for ${notional:.2f}')
        except Exception as e:
            print(f'Order failed for {ticker}: {e}')

    return {'status': 'success', 'orders_executed': executed}
