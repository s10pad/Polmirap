# REVIEW.md — Weekly Roster Review

This file documents the weekly review process and holds the template the AI uses when generating proposals. The latest review proposal is stored in Redis (`mirror:review_proposal`) and shown live on the dashboard ROSTER tab. This file provides the format reference and history context.

---

## How the weekly review works

Every Monday at 6am ET, the system:

1. Fetches recent news and performance data for each current roster member via Brave Search.
2. Searches for new potential candidates who have recently disclosed trades.
3. Sends all of this to Claude with the current roster (names, weights, performance percentages).
4. Claude returns a JSON proposal with up to 3 changes.
5. The proposal is stored in Redis and sent to you via Telegram.
6. Nothing changes until you reply `APPROVE` (applies all changes) or click the dashboard button.

The review is limited to 3 changes per week to prevent rapid turnover. Stability in the roster is valuable — consistent tracking of the same people over time builds reliable weight data.

---

## Review proposal structure

Each proposal contains:

- **summary**: A 2-3 sentence plain English explanation of what the AI is recommending and why.
- **changes**: A list of up to 3 individual change objects.

Each change object contains:
- `action`: One of `keep`, `remove`, `add`, or `weight_update`
- `name`: The person's full name
- `reason`: 1-2 sentences explaining the recommendation
- `category`: (for `add` actions only) `politician`, `ceo`, `athlete`, or `public_figure`
- `suggested_weight`: (for `add` and `weight_update` actions) a float between 0.5 and 1.6

`keep` actions are informational — they document that the AI reviewed a member and recommends no change. They do not count against the 3-change limit.

---

## Example review proposal

```
Summary: Nancy Pelosi continues to show strong disclosed trade performance with 3 new 
filings this week. Recommending removal of John Smith due to no new disclosures in 90 
days and negative performance. Adding Elon Musk as a new candidate based on recent 
disclosed purchases with strong outcomes.

Changes:
- KEEP Nancy Pelosi: Consistent filer, weight performing well, recent NVDA purchase 
  disclosed at +18% in 30 days.
- REMOVE John Smith: No filings in 90+ days, cumulative performance -8.2% on 
  mirrored trades. Replacing with higher-signal candidate.
- ADD Elon Musk (category: ceo, suggested_weight: 1.1): Multiple recent disclosed 
  purchases in AI/tech sector with strong outcomes. High public profile ensures 
  rapid disclosure pickup.
```

---

## Instructions for the AI

When generating a review proposal, Claude should:

1. Prioritize removing members with zero recent disclosures (90+ days since last trade found) or sustained negative performance on mirrored trades.
2. Prioritize adding members who have shown at least 2 recent disclosed trades in the last 60 days, ideally with positive outcomes visible in news.
3. Suggest weight increases for members whose recent trades have outperformed (up to +0.2 from current weight, capped at 1.6).
4. Suggest weight decreases for members whose recent trades have underperformed but who should remain on the roster (down to -0.2 from current weight, floored at 0.5).
5. Maintain diversity: no more than 5 politicians, no more than 3 from any single sector focus.
6. Never propose changes that would leave the roster below 5 active members.
7. Always include a summary that the owner can read in 15 seconds to understand the recommendation.

---

## Latest Review

*No review has been run yet. The first weekly review will run automatically on the next Monday at 6am ET after the system is deployed and the roster is bootstrapped.*

After the first review runs, the proposal details will be stored in Redis and visible on the dashboard ROSTER tab. This section of REVIEW.md is not auto-updated — it is a static reference document. The live proposal is always in the dashboard.
