"""
Scoring engine — takes raw disclosures and AI-parsed trades, produces ranked signals.
Applies conviction multipliers, position sizing, and sector caps.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional
from strategy import (
    compute_score,
    compute_position_size,
    get_conviction_multiplier,
    TradeProposal,
    SIGNAL_SCORE_THRESHOLD,
)
from memory import get_roster, get_open_positions_meta

logger = logging.getLogger(__name__)


def group_trades_by_ticker(parsed_trades: list) -> dict:
    """
    Group a flat list of trade dicts by ticker symbol.
    Each trade dict must have: ticker, action (buy/sell), name, portfolio_pct, sector.
    Returns a dict: ticker -> list of trades.
    """
    grouped = {}
    for trade in parsed_trades:
        t = trade.get("ticker", "").upper()
        if not t:
            continue
        grouped.setdefault(t, []).append(trade)
    return grouped


def compute_sector_exposures(positions: list) -> dict:
    """
    Calculate current portfolio exposure per sector from open Alpaca positions.
    Returns dict: sector -> % of portfolio.
    positions: list of Alpaca position objects.
    """
    if not positions:
        return {}
    total_value = sum(float(p.market_value) for p in positions)
    if total_value <= 0:
        return {}
    meta = get_open_positions_meta()
    exposures = {}
    for p in positions:
        sector = meta.get(p.symbol, {}).get("sector", "Unknown")
        pct = (float(p.market_value) / total_value) * 100
        exposures[sector] = exposures.get(sector, 0.0) + pct
    return exposures


def score_all_tickers(
    parsed_trades: list,
    portfolio_equity: float,
    open_positions: list,
    ai_reasoner,  # callable: (ticker, trades, context) -> (reasoning, midpoint_pct, sector)
) -> list:
    """
    Score all tickers from parsed trade disclosures and return ranked TradeProposal list.
    Only returns net-buy signals above SIGNAL_SCORE_THRESHOLD.

    - parsed_trades: list of {'name', 'ticker', 'action', 'portfolio_pct', 'sector'} dicts
    - portfolio_equity: owner's Alpaca account value
    - open_positions: list of Alpaca position objects
    - ai_reasoner: function to get AI reasoning and midpoint % for a ticker
    """
    roster = get_roster()
    person_weights = {m["name"]: m.get("weight", 1.0) for m in roster}
    grouped = group_trades_by_ticker(parsed_trades)
    sector_exposures = compute_sector_exposures(open_positions)

    proposals = []
    for ticker, trades in grouped.items():
        buy_trades = [t for t in trades if t.get("action") == "buy"]
        if not buy_trades:
            continue  # skip net-sell or neutral

        score = compute_score(trades, person_weights)
        if score <= SIGNAL_SCORE_THRESHOLD:
            continue

        conviction = len(buy_trades)
        buyers = [
            {"name": t["name"], "portfolio_pct": t.get("portfolio_pct", 0.0)}
            for t in buy_trades
        ]

        try:
            reasoning, midpoint_pct, sector = ai_reasoner(ticker, trades, {
                "score": score,
                "conviction": conviction,
                "buyers": buyers,
            })
        except Exception as e:
            logger.error(f"AI reasoner failed for {ticker}: {e}")
            reasoning = "AI reasoning unavailable."
            midpoint_pct = trades[0].get("portfolio_pct", 0.5)
            sector = trades[0].get("sector", "Unknown")

        current_sector_exposure = sector_exposures.get(sector, 0.0)
        position_pct, position_usd, cap_note = compute_position_size(
            midpoint_pct, conviction, portfolio_equity, current_sector_exposure, sector
        )

        if position_pct <= 0:
            logger.info(f"Skipping {ticker} — sector cap would give 0% allocation ({cap_note})")
            continue

        if cap_note:
            reasoning += f" (Size adjusted: {cap_note}.)"

        proposals.append(
            TradeProposal(
                ticker=ticker,
                action="BUY",
                score=score,
                conviction=conviction,
                buyers=buyers,
                position_pct=position_pct,
                position_usd=position_usd,
                sector=sector,
                reasoning=reasoning,
                signal_id=str(uuid.uuid4())[:8],
            )
        )

    proposals.sort(key=lambda p: p.score, reverse=True)
    return proposals
