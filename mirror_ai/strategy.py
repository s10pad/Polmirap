"""
Strategy rules — position sizing, conviction tiers, stop-loss, sector caps.
All rules are defined here. Scorer and agent read from this module.
"""

import os
from dataclasses import dataclass
from typing import Optional


# Load configurable limits from env
VETO_WINDOW_HOURS = int(os.getenv("VETO_WINDOW_HOURS", "2"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "15"))
MAX_POSITION_PCT = float(os.getenv("MAX_POSITION_PCT", "7.0"))
SECTOR_CAP_PCT = float(os.getenv("SECTOR_CAP_PCT", "20.0"))
SIGNAL_SCORE_THRESHOLD = 0.5  # Minimum score to surface a signal
FULL_MODE_AUTO_THRESHOLD = 8.0  # Score above this triggers immediate execution in FULL mode

# Conviction tiers: how many people are buying the same ticker
CONVICTION_CAPS = {
    1: 1.0,   # 1 person = max 1% of portfolio
    2: 2.5,   # 2 people = max 2.5%
    3: 5.0,   # 3+ people = max 5.0%
}

# Conviction score multipliers
CONVICTION_MULTIPLIERS = {
    2: 1.2,
    3: 1.5,
}

# Weight bounds
WEIGHT_MIN = 0.5
WEIGHT_MAX = 1.6
WEIGHT_GAIN = 0.05   # profitable trade
WEIGHT_LOSS = 0.10   # losing trade


@dataclass
class TradeProposal:
    """A fully-scored trade signal ready for owner review or execution."""
    ticker: str
    action: str               # BUY | SELL
    score: float
    conviction: int           # number of roster members buying
    buyers: list              # list of names with their portfolio %
    position_pct: float       # % of owner portfolio to allocate
    position_usd: float       # dollar amount at current equity
    sector: str
    reasoning: str            # AI-generated explanation
    signal_id: str            # unique ID for tracking veto/approval


def get_conviction_cap(conviction: int) -> float:
    """Return the max portfolio % allowed for a given conviction level."""
    if conviction >= 3:
        return CONVICTION_CAPS[3]
    return CONVICTION_CAPS.get(conviction, CONVICTION_CAPS[1])


def get_conviction_multiplier(conviction: int) -> float:
    """Return the score multiplier based on how many people are buying."""
    if conviction >= 3:
        return CONVICTION_MULTIPLIERS[3]
    return CONVICTION_MULTIPLIERS.get(conviction, 1.0)


def compute_position_size(
    disclosed_range_midpoint_pct: float,
    conviction: int,
    portfolio_equity: float,
    current_sector_exposure: float,
    sector: str,
) -> tuple[float, float, str]:
    """
    Calculate the owner's position size for a mirrored trade.

    Returns (position_pct, position_usd, note) where note explains any cap applied.
    - disclosed_range_midpoint_pct: AI's estimate of the trade as % of the person's portfolio
    - conviction: number of roster members buying this ticker
    - portfolio_equity: owner's total Alpaca account value
    - current_sector_exposure: % of owner portfolio already in this sector
    - sector: sector name for cap checking
    """
    cap = get_conviction_cap(conviction)
    raw_pct = min(disclosed_range_midpoint_pct, cap)
    note = ""

    # Apply hard max
    if raw_pct > MAX_POSITION_PCT:
        raw_pct = MAX_POSITION_PCT
        note = f"Capped at hard max {MAX_POSITION_PCT}%"

    # Check sector concentration
    projected_sector = current_sector_exposure + raw_pct
    if projected_sector > SECTOR_CAP_PCT:
        available = max(0.0, SECTOR_CAP_PCT - current_sector_exposure)
        raw_pct = available
        note = f"Sector cap hit ({sector} at {current_sector_exposure:.1f}%); reduced to {raw_pct:.1f}%"

    position_usd = round((raw_pct / 100) * portfolio_equity, 2)
    return round(raw_pct, 4), position_usd, note


def compute_score(trades: list, person_weights: dict) -> float:
    """
    Score a ticker based on net buy pressure and roster weights.

    trades: list of dicts with 'name' and 'action' ('buy' or 'sell')
    person_weights: dict mapping name -> weight float

    Returns a float score. Only positive scores (net buys) are meaningful.
    """
    net = 0.0
    for t in trades:
        w = person_weights.get(t["name"], 1.0)
        if t["action"] == "buy":
            net += w
        elif t["action"] == "sell":
            net -= w

    conviction = sum(1 for t in trades if t["action"] == "buy")
    multiplier = get_conviction_multiplier(conviction)
    return round(net * multiplier, 4)


def update_weight_after_trade(current_weight: float, profitable: bool) -> float:
    """
    Adjust a roster member's weight after a 30-day trade cycle completes.
    Profitable trades increase weight; losses decrease it.
    """
    if profitable:
        new_weight = min(current_weight + WEIGHT_GAIN, WEIGHT_MAX)
    else:
        new_weight = max(current_weight - WEIGHT_LOSS, WEIGHT_MIN)
    return round(new_weight, 4)


def is_stop_loss_triggered(entry_price: float, current_price: float) -> bool:
    """Return True if the position has dropped below the stop loss threshold."""
    if entry_price <= 0:
        return False
    drop_pct = ((entry_price - current_price) / entry_price) * 100
    return drop_pct >= STOP_LOSS_PCT


def kelly_fraction(win_rate: float, avg_win_pct: float, avg_loss_pct: float) -> float:
    """
    Kelly Criterion — informational reference only. Not used for actual position sizing.
    Returns the theoretically optimal fraction of bankroll to risk given historical stats.

    win_rate: 0.0–1.0 (e.g. 0.6 for 60% win rate)
    avg_win_pct: average winning trade return as decimal (e.g. 0.05 for 5%)
    avg_loss_pct: average losing trade loss as decimal (e.g. 0.03 for 3% loss)
    """
    if avg_loss_pct <= 0:
        return 0.0
    odds = avg_win_pct / avg_loss_pct
    kelly = win_rate - ((1 - win_rate) / odds)
    return round(max(0.0, kelly), 4)
