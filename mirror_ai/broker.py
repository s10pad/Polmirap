"""
Broker abstraction — wraps Alpaca today, per-user creds in Phase 7.
get_broker(uid) returns an AlpacaBroker. uid is ignored until Phase 7.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AlpacaBroker:
    """Alpaca trading client with clean dict-based returns."""

    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        from alpaca.trading.client import TradingClient
        self._client = TradingClient(api_key, api_secret, paper=paper)
        self._paper = paper

    @property
    def is_paper(self) -> bool:
        return self._paper

    def get_account(self) -> dict:
        a = self._client.get_account()
        return {
            "equity": float(a.equity or 0),
            "cash": float(a.cash or 0),
            "buying_power": float(a.buying_power or 0),
            "portfolio_value": float(a.portfolio_value or 0),
            "paper": self._paper,
        }

    def get_equity(self) -> float:
        return self.get_account()["equity"]

    def get_positions(self) -> list:
        return [
            {
                "symbol": p.symbol,
                "qty": float(p.qty or 0),
                "avg_entry_price": float(p.avg_entry_price or 0),
                "current_price": float(p.current_price or 0),
                "market_value": float(p.market_value or 0),
                "unrealized_pl": float(p.unrealized_pl or 0),
                "unrealized_plpc": float(p.unrealized_plpc or 0),
            }
            for p in self._client.get_all_positions()
        ]

    def submit_market_order(self, ticker: str, notional: float, side: str) -> dict:
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        order = self._client.submit_order(
            MarketOrderRequest(
                symbol=ticker,
                notional=notional,
                side=order_side,
                time_in_force=TimeInForce.DAY,
            )
        )
        return {
            "id": str(order.id),
            "ticker": ticker,
            "side": side,
            "notional": notional,
            "status": str(order.status),
            "filled_avg_price": float(order.filled_avg_price or 0),
            "filled_qty": float(order.filled_qty or 0),
        }

    def get_raw_client(self):
        """Underlying TradingClient for backward compat with existing scheduler code."""
        return self._client


_instance: Optional[AlpacaBroker] = None


def get_broker(uid: str = None) -> AlpacaBroker:
    """
    Return the AlpacaBroker for this operator.
    uid is a no-op today — Phase 7 will look up per-user creds from Firestore.
    """
    global _instance
    if _instance is None:
        _instance = AlpacaBroker(
            api_key=os.getenv("ALPACA_KEY", ""),
            api_secret=os.getenv("ALPACA_SECRET", ""),
            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true",
        )
    return _instance
