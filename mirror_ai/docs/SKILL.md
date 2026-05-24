# SKILL.md — How Mirror AI Makes Decisions

This document explains the scoring formula, position sizing logic, and signal quality rules in plain English, with worked examples.

---

## How scoring works

Every trade signal starts with a raw net buy score and then gets multiplied by a conviction bonus.

### Step 1: Net buy pressure

For each ticker, add up the weights of everyone buying and subtract the weights of everyone selling.

```
net = sum(weight for each buyer) - sum(weight for each seller)
```

Weights start at 1.0 for new roster members. They change over time based on whether their disclosed trades turned out to be profitable (see Weight Decay below).

### Step 2: Conviction multiplier

If multiple people are buying the same ticker at the same time, the score gets multiplied:

| Number of buyers | Multiplier |
|---|---|
| 1 | 1.0x (no bonus) |
| 2 | 1.2x |
| 3 or more | 1.5x |

### Step 3: Final score

```
score = net × multiplier
```

Only signals with a score above 0.5 are surfaced. Signals below this are discarded.

### Worked example

Suppose the ticker is NVDA and the following trades are detected:

- **Senator A** (weight 1.2): bought NVDA (2% of their portfolio)
- **CEO B** (weight 1.0): bought NVDA (1% of their portfolio)
- **Athlete C** (weight 0.9): sold NVDA

```
net = 1.2 + 1.0 - 0.9 = 1.3
conviction = 2 buyers → multiplier = 1.2
score = 1.3 × 1.2 = 1.56
```

Score 1.56 is above the 0.5 threshold. This signal is surfaced.

---

## How position sizes are derived from disclosure ranges

STOCK Act filings report trades in ranges: $1,001–$15,000 / $15,001–$50,000 / $50,001–$100,000 / etc. Claude estimates the midpoint of the likely range and converts it to an estimated percentage of the person's portfolio.

For example: if Senator A is estimated to have a $5M portfolio and disclosed a $15,001–$50,000 purchase, the midpoint is $32,500, which is approximately 0.65% of their portfolio.

This estimated percentage is passed to the position sizing formula.

### Conviction caps

Your position size is capped based on how many people are buying:

| Buyers | Max % of your portfolio |
|---|---|
| 1 person | 1.0% |
| 2 people | 2.5% |
| 3+ people | 5.0% |

The actual size is the minimum of: the estimated midpoint percentage AND the conviction cap AND the hard max AND the sector availability.

### Hard max

No single position can exceed `MAX_POSITION_PCT` (default 7%) of your portfolio, regardless of conviction. This is a hard ceiling that overrides all other calculations.

### Worked example

Portfolio equity: $50,000
Ticker: NVDA
Buyers: 2 (Senator A at 0.65% of their portfolio, CEO B at 0.8%)
Sector: Technology
Current Technology exposure: 12% of your portfolio
Sector cap: 20%

```
Conviction cap for 2 buyers = 2.5%
Estimated midpoint = average(0.65, 0.8) = 0.725%
Raw position = min(0.725, 2.5) = 0.725%
Hard max check: 0.725% < 7% → no cap applied
Sector check: 12% + 0.725% = 12.725% < 20% → no cap applied
Final position = 0.725% of $50,000 = $362.50
```

---

## Confidence decay: what it is

"Confidence decay" is implemented as **weight adjustment** based on trade outcome, evaluated over a 30-day window after the disclosure.

After 30 days:
- If the trade was profitable (positive P&L): the person's weight increases by 0.05
- If the trade was losing (negative P&L): the person's weight decreases by 0.10

Losses penalize more than wins reward, which means someone needs a consistent winning track record to reach high weight. This is intentional — a few big wins can be luck, but consistent losses should reduce influence quickly.

**Weight bounds**: minimum 0.5, maximum 1.6

### Worked example

A roster member starts with weight 1.0.

- Trade 1: AAPL → +12% in 30 days → profitable → weight becomes 1.05
- Trade 2: TSLA → +8% in 30 days → profitable → weight becomes 1.10
- Trade 3: GME → -22% in 30 days → loss → weight becomes 1.00
- Trade 4: MSFT → +5% in 30 days → profitable → weight becomes 1.05

Over time, consistent winners drift toward 1.6 and consistent losers drift toward 0.5, where they become candidates for removal at the weekly review.

---

## How Brave Search is used

Every day at 7:30am ET, the system runs search queries for each roster member. Three query templates per person:

1. `{name} stock trade disclosure 2024 2025`
2. `{name} STOCK Act filing bought sold`
3. `{name} SEC filing stock purchase`

Each query returns up to 5 results (title, URL, description). Claude then reads all 15 results per person and extracts any structured trade events it finds.

For the weekly review, additional queries search for news about each member's trading performance and for new potential candidates to add to the roster.

### What we look for in results

Strong signals in search results:
- Explicit mention of a specific ticker being purchased
- A dollar range consistent with STOCK Act format ($15,001–$50,000)
- A recent date (within the last 30–60 days)
- Multiple independent sources reporting the same trade

Weak signals (discarded or scored low):
- Vague mentions of "technology investments" without a ticker
- News about trades from more than 90 days ago
- Sources that appear speculative rather than citing official filings

---

## What makes a strong vs weak signal

### Strong signal characteristics
- 3+ roster members buying the same ticker independently
- Each buyer has a weight above 1.0 (track record of profitable disclosures)
- Disclosed trade date is recent (within last 30 days)
- Multiple independent sources confirm the trade
- Sector is not already near the concentration cap
- Score above 3.0

### Weak signal characteristics
- Only 1 person buying, with a weight near 0.5
- Trade date is old (60+ days ago)
- Only one source, which appears to be speculative commentary
- Sector is already at 15%+ concentration in your portfolio
- Score between 0.5 and 1.0

You can observe signal quality in the FEED tab. The score and reasoning are shown for every signal. Signals you skip repeatedly can be analyzed to tune the scoring thresholds in `strategy.py`.

---

## How sector caps are enforced

Before calculating the final position size, the system calculates your current exposure per sector based on open Alpaca positions and the sector tags stored for each position.

If adding the proposed position would push that sector above `SECTOR_CAP_PCT` (default 20%), the position is reduced to fit within the remaining headroom.

### Example

- Technology sector cap: 20%
- Current Technology exposure: 17%
- Proposed NVDA position: 2.5% of portfolio
- Available headroom: 20% - 17% = 3%
- Since 2.5% < 3%, the full position is allowed

Another example:
- Current Technology exposure: 19%
- Proposed NVDA position: 2.5%
- Available headroom: 1%
- Position is reduced to 1%
- Reasoning note appended: "Sector cap hit (Technology at 19.0%); reduced to 1.0%"

If the headroom is 0% (sector is already at the cap), the signal is discarded entirely. You will see "Skipping TICKER — sector cap would give 0% allocation" in the logs.
