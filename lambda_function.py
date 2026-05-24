"""
Lambda auto-trader — runs on CloudWatch schedule (weekdays 09:00 ET).
Pulls fresh politician trades from Capitol Trades HTML, mirrors BUY/SELL via Alpaca.
Credentials stored in AWS Secrets Manager under 'Fintech/PoliticianTrading'.
"""
import os, json, re, time, boto3, requests
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
}

POLITICIANS = {
    'pelosi':     {'name': 'Nancy Pelosi',          'ct_id': 'P000197', 'weight': 1.6},
    'schultz':    {'name': 'Debbie Schultz',        'ct_id': 'S001565', 'weight': 1.5},
    'williams':   {'name': 'Roger Williams',        'ct_id': 'W000816', 'weight': 1.4},
    'wyden':      {'name': 'Ron Wyden',              'ct_id': 'W000779', 'weight': 1.3},
    'sessions':   {'name': 'Pete Sessions',          'ct_id': 'S000250', 'weight': 1.2},
    'collins':    {'name': 'Susan Collins',          'ct_id': 'C001035', 'weight': 1.3},
    'tuberville': {'name': 'Tommy Tuberville',       'ct_id': 'T000278', 'weight': 1.3},
    'greene':     {'name': 'Marjorie Taylor Greene', 'ct_id': 'G000596', 'weight': 1.1},
}

PROCESSED_TABLE = os.getenv('PROCESSED_TABLE', 'MirrorAI-Processed')
TRADE_PCT       = float(os.getenv('TRADE_PCT', '0.005'))  # 0.5% of equity per trade


def fetch_trades(ct_id, name, pages=2):
    trades = []
    for page in range(1, pages + 1):
        url = f'https://www.capitoltrades.com/politicians/{ct_id}?page={page}'
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                break
            html = r.text
        except Exception as e:
            print(f'{name} page {page}: {e}')
            break

        rows = re.findall(r'([A-Z]{1,5}):US.*?(?:>\s*(buy|sell)\s*<)', html, re.DOTALL | re.IGNORECASE)
        for ticker, side in rows:
            trades.append({'ticker': ticker.upper(), 'side': side.lower(), 'name': name})

        if len(rows) < 5:
            break
        time.sleep(0.5)
    return trades


def already_processed(ddb, ticker, side, name):
    key = ticker + '_' + side + '_' + name.split()[-1]
    try:
        resp = ddb.get_item(TableName=PROCESSED_TABLE, Key={'id': {'S': key}})
        return 'Item' in resp
    except Exception:
        return False


def mark_processed(ddb, ticker, side, name):
    key = ticker + '_' + side + '_' + name.split()[-1]
    try:
        import datetime as _dt
        ttl = int(_dt.datetime.utcnow().timestamp()) + 7 * 86400  # expire after 7 days
        ddb.put_item(TableName=PROCESSED_TABLE, Item={'id': {'S': key}, 'ttl': {'N': str(ttl)}})
    except Exception as e:
        print(f'DDB write failed: {e}')


def lambda_handler(event, context):
    # Load credentials
    sm    = boto3.client('secretsmanager')
    creds = json.loads(sm.get_secret_value(SecretId='Fintech/PoliticianTrading')['SecretString'])
    is_paper = os.getenv('DRY_RUN', 'true').lower() == 'true'

    client = TradingClient(creds['ALPACA_KEY'], creds['ALPACA_SECRET'], paper=is_paper)
    acct   = client.get_account()
    equity = float(acct.equity)
    notional = max(10.0, round(equity * TRADE_PCT, 2))
    print(f'Equity ${equity:,.0f}  |  Trade size ${notional:.2f}  |  Paper={is_paper}')

    ddb = boto3.client('dynamodb')
    executed = 0
    skipped  = 0

    for key, info in POLITICIANS.items():
        print(f'Fetching {info["name"]}...')
        trades = fetch_trades(info['ct_id'], info['name'])
        for t in trades:
            ticker = t['ticker']
            side   = t['side']
            name   = t['name']

            if already_processed(ddb, ticker, side, name):
                skipped += 1
                continue

            alpaca_side = OrderSide.BUY if side == 'buy' else OrderSide.SELL
            try:
                if alpaca_side == OrderSide.SELL:
                    # Only sell if we hold the position
                    positions = {p.symbol: p for p in client.get_all_positions()}
                    if ticker not in positions:
                        mark_processed(ddb, ticker, side, name)
                        continue
                    req = MarketOrderRequest(
                        symbol=ticker, qty=float(positions[ticker].qty),
                        side=OrderSide.SELL, time_in_force=TimeInForce.DAY,
                    )
                else:
                    req = MarketOrderRequest(
                        symbol=ticker, notional=notional,
                        side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
                    )
                client.submit_order(req)
                mark_processed(ddb, ticker, side, name)
                executed += 1
                print(f'  {side.upper()} {ticker} ${notional:.2f} — {name}')
            except Exception as e:
                print(f'  Order failed {ticker}: {e}')

    print(f'Done — {executed} orders, {skipped} skipped (already processed)')
    return {'status': 'success', 'orders_executed': executed, 'skipped': skipped}
