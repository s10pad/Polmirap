import os
import json
import requests
import boto3
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from database import DuplicateHandler
from strategy import MirrorStrategy

def lambda_handler(event, context):
    # 1. Fetch Credentials
    sm = boto3.client('secretsmanager')
    resp = sm.get_secret_value(SecretId="Fintech/PoliticianTrading")
    creds = json.loads(resp)
    
    # 2. Setup (Targeting high-frequency PTR disclosures) 
    is_paper = os.getenv("DRY_RUN") == "True"
    trading_client = TradingClient(creds, creds, paper=is_paper)
    db = DuplicateHandler()
    strat = MirrorStrategy(float(trading_client.get_account().buying_power))
    
    # 3. Data Pull: House & Senate (Aggregated S3 Pools) [4, 5]
    house_url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
    senate_url = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"
    
    all_trades = requests.get(house_url).json() + requests.get(senate_url).json()
    
    # Top 7 Target Politicians 
    targets =
    executed = 0

    for t in all_trades[:50]: # Scan most recent 50 filings
        # VALIDITY: Only process Periodic Transaction Reports (PTR) to minimize lag 
        if t.get('filing_type', 'P')!= 'P': continue
        
        name = t.get('representative', t.get('senator', ''))
        ticker = t.get('ticker')

        if any(target in name for target in targets) and ticker and ticker!= "--":
            # Idempotency: Deduplicate using Name + Ticker + Date [2, 6]
            internal_id = f"{ticker}_{name.split()[-1]}_{t['transaction_date']}".replace('/', '')
            
            if not db.already_processed(internal_id):
                notional = strat.calculate_notional(t['amount'])
                
                if notional >= 1.0: # Alpaca fractional minimum
                    try:
                        side = OrderSide.BUY if "purchase" in t['type'].lower() else OrderSide.SELL
                        order = MarketOrderRequest(
                            symbol=ticker, notional=notional, side=side, time_in_force=TimeInForce.GTC
                        )
                        trading_client.submit_order(order)
                        db.mark_processed(internal_id, t)
                        executed += 1
                        print(f"Mirrored {name}: {side} {ticker} for ${notional}")
                    except Exception as e:
                        print(f"Error executing {ticker}: {e}")

    return {"status": "success", "orders": executed}