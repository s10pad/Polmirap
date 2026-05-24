"""
Core AI reasoning engine — Gemini 3.5 Flash via google-genai SDK (Google I/O 2026).

Daily analysis uses a multi-turn Gemini chat session (Antigravity-style agentic loop):
the model sees all roster members' disclosures at once, cross-references trades,
and produces holistic signals rather than processing each person in isolation.
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import Optional

from google import genai
from google.genai import types

from fetcher import fetch_all_disclosures, fetch_roster_candidates, fetch_weekly_review_data
from memory import append_changelog, get_roster, set_review_proposal, get_autonomy_mode
from strategy import FULL_MODE_AUTO_THRESHOLD

logger = logging.getLogger(__name__)

MODEL = "gemini-3.5-flash"

_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    """Return a singleton Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
    return _client


def _extract_json(text: str) -> str:
    """Pull JSON out of a response that may be wrapped in markdown code fences."""
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    return match.group(1) if match else text.strip()


def call_gemini(system: str, prompt: str, max_tokens: int = 2000) -> str:
    """
    Single-turn Gemini call. Returns the text response or '' on failure.
    Used for discrete tasks: parsing, reasoning, proposals.
    """
    try:
        response = get_client().models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=0.2,
            ),
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] ERROR AI_CALL — Gemini unavailable: {e}"
        )
        return ""


def parse_disclosures_to_trades(person_name: str, raw_results: list) -> list:
    """
    Use Gemini to extract structured trade events from raw Brave Search results.
    Returns list of dicts: {ticker, action, portfolio_pct, sector, date, source}.
    """
    if not raw_results:
        return []

    snippets = "\n".join(
        f"- {r['title']}: {r.get('description', '')}" for r in raw_results[:8]
    )

    system = (
        "You are a financial disclosure parser. Extract stock trade events from web search snippets. "
        "Return ONLY a JSON array. Each item: {ticker, action (buy/sell), portfolio_pct (estimated % "
        "of their portfolio, float), sector (e.g. Technology), date (YYYY-MM-DD or best guess), source}. "
        "If no clear trades found, return []. No explanation, just JSON."
    )
    prompt = f"Person: {person_name}\n\nSearch results:\n{snippets}"

    response = call_gemini(system, prompt, max_tokens=1000)
    try:
        trades = json.loads(_extract_json(response))
        if isinstance(trades, list):
            for t in trades:
                t["name"] = person_name
            return trades
    except (json.JSONDecodeError, ValueError):
        logger.warning(f"Could not parse trades JSON for {person_name}")
    return []


def reason_about_signal(ticker: str, trades: list, context: dict) -> tuple[str, float, str]:
    """
    Generate Gemini reasoning for a trade signal.
    Returns (reasoning_text, estimated_midpoint_pct, sector).
    """
    buyers_text = ", ".join(
        f"{t['name']} ({t.get('portfolio_pct', '?')}% of their portfolio)"
        for t in trades if t.get("action") == "buy"
    )
    system = (
        "You are a trade signal analyst. Given a stock ticker and who is buying it, "
        "write 2-3 sentences explaining why this is a compelling signal. "
        "Then on a new line write: SECTOR: <sector name>. "
        "Then on a new line write: MIDPOINT_PCT: <float between 0.1 and 3.0>. "
        "The midpoint_pct is your estimate of the position as % of the buyer's portfolio."
    )
    prompt = (
        f"Ticker: {ticker}\n"
        f"Buyers: {buyers_text}\n"
        f"Conviction score: {context.get('score', 0):.2f}\n"
        f"Number buying: {context.get('conviction', 0)}"
    )

    response = call_gemini(system, prompt, max_tokens=300)
    if not response:
        return "Signal generated from disclosed trades.", 0.5, "Unknown"

    lines = response.strip().split("\n")
    reasoning_lines = []
    sector = "Unknown"
    midpoint_pct = 0.5

    for line in lines:
        if line.startswith("SECTOR:"):
            sector = line.replace("SECTOR:", "").strip()
        elif line.startswith("MIDPOINT_PCT:"):
            try:
                midpoint_pct = float(line.replace("MIDPOINT_PCT:", "").strip())
            except ValueError:
                pass
        else:
            reasoning_lines.append(line)

    reasoning = " ".join(reasoning_lines).strip() or "Based on disclosed trades."
    return reasoning, midpoint_pct, sector


def discover_initial_roster(search_results: list) -> list:
    """
    Use Gemini to select the 10 best public figures for the initial roster.
    Returns list of member dicts ready for roster.bootstrap_roster().
    """
    snippets = "\n".join(
        f"- {r['title']}: {r.get('description', '')}" for r in search_results[:40]
    )

    system = (
        "You are building a roster of public figures to mirror in a stock trading system. "
        "Select exactly 10 people based on: consistent disclosed trade outperformance, "
        "recency of trades, diversity (not all politicians — include CEOs, athletes, public figures), "
        "and public availability of their disclosures. "
        "Return ONLY a JSON array of 10 objects: "
        "{name, category (politician|ceo|athlete|public_figure), why_added (1-2 sentences), weight (0.8-1.2 float)}. "
        "No explanation, just JSON."
    )
    prompt = f"Search results about top trading public figures:\n{snippets}"

    response = call_gemini(system, prompt, max_tokens=2000)
    if not response:
        return []

    try:
        candidates = json.loads(_extract_json(response))
        if isinstance(candidates, list):
            return candidates[:10]
    except (json.JSONDecodeError, ValueError):
        logger.error("Could not parse roster candidates JSON from Gemini")
    return []


def run_daily_analysis() -> list:
    """
    Agentic daily analysis using a multi-turn Gemini chat session.

    Turn 1: Gemini ingests all roster disclosures at once and extracts every trade
            holistically — catching when multiple members bought the same ticker.
    Turn 2 (fallback): If turn 1 JSON parse fails, falls back to per-member parsing.
    Python then scores and sizes positions via the existing scorer module.
    """
    from scorer import score_all_tickers

    roster = get_roster()
    if not roster:
        logger.warning("Roster empty — skipping daily analysis")
        return []

    append_changelog(
        f"[{datetime.now().strftime('%Y-%m-%d')}] DAILY_RUN — "
        f"Starting Gemini agentic analysis for {len(roster)} roster members."
    )

    raw_disclosures = fetch_all_disclosures(roster)

    # Build unified context: all members + snippets in one payload
    disclosure_context = {}
    for name, disclosure in raw_disclosures.items():
        results = disclosure.get("results", []) if isinstance(disclosure, dict) else disclosure
        disclosure_context[name] = [
            f"{r.get('title', '')}: {r.get('description', '')}"
            for r in results[:6]
        ]

    # Multi-turn chat: model sees the full roster simultaneously
    chat = get_client().chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are an expert financial disclosure analyst. You receive search result snippets "
                "about stock disclosures from politicians, CEOs, athletes, and public figures. "
                "Extract every stock trade mentioned and group them by ticker so confluence is visible."
            ),
            temperature=0.1,
        ),
    )

    turn1_prompt = (
        f"Roster members: {json.dumps([m['name'] for m in roster])}\n\n"
        f"Recent disclosure search results per member:\n"
        f"{json.dumps(disclosure_context, indent=2)}\n\n"
        "Extract every stock trade from the snippets above. "
        "Return ONLY a JSON array — no prose, no fences: "
        "[{name, ticker, action (buy/sell), portfolio_pct (float), sector, date, source}]"
    )

    all_trades = []
    try:
        resp1 = chat.send_message(turn1_prompt)
        all_trades = json.loads(_extract_json(resp1.text))
        if not isinstance(all_trades, list):
            all_trades = []
    except Exception as e:
        logger.error(f"Gemini agentic turn 1 failed ({e}) — falling back to per-member parsing")
        for name, disclosure in raw_disclosures.items():
            results = disclosure.get("results", []) if isinstance(disclosure, dict) else disclosure
            all_trades.extend(parse_disclosures_to_trades(name, results))

    if not all_trades:
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] DAILY_RUN — No new trades found."
        )
        return []

    try:
        from alpaca.trading.client import TradingClient
        alpaca = TradingClient(
            os.getenv("ALPACA_KEY", ""),
            os.getenv("ALPACA_SECRET", ""),
            paper=os.getenv("ALPACA_PAPER", "true").lower() == "true",
        )
        account = alpaca.get_account()
        portfolio_equity = float(account.equity)
        open_positions = alpaca.get_all_positions()
    except Exception as e:
        logger.error(f"Alpaca account fetch failed: {e}")
        portfolio_equity = 10000.0
        open_positions = []

    proposals = score_all_tickers(
        all_trades, portfolio_equity, open_positions, reason_about_signal
    )

    append_changelog(
        f"[{datetime.now().strftime('%Y-%m-%d')}] DAILY_RUN — "
        f"Gemini analysis complete. {len(proposals)} signals generated."
    )
    return proposals


def run_weekly_review() -> Optional[dict]:
    """
    Generate the weekly roster review proposal using Gemini and web search data.
    Stores proposal in Firestore and returns it. Called every Monday at 6am.
    """
    roster = get_roster()
    review_data = fetch_weekly_review_data(roster)

    roster_summary = "\n".join(
        f"- {m['name']} ({m['category']}, weight={m.get('weight', 1.0)}, "
        f"perf={m.get('performance_since_added', 0.0):.1f}%)"
        for m in roster
    )

    new_candidate_snippets = "\n".join(
        f"- {r['title']}: {r.get('description', '')}"
        for r in review_data.get("_new_candidates", [])[:10]
    )

    member_news = {}
    for m in roster:
        name = m["name"]
        snippets = "\n".join(
            f"- {r['title']}: {r.get('description', '')}"
            for r in review_data.get(name, [])[:5]
        )
        member_news[name] = snippets

    member_news_text = "\n\n".join(
        f"### {name}\n{news}" for name, news in member_news.items()
    )

    system = (
        "You are reviewing a stock trade mirroring roster. "
        "Propose up to 3 changes (keep/remove/add/weight_update). "
        "Return ONLY a JSON object: "
        "{summary: str, changes: [{action: keep|remove|add|weight_update, name: str, "
        "reason: str, category: str (for add), suggested_weight: float (for add/weight_update)}]}. "
        "Maximum 3 changes. Prioritize performance, recency, and diversity."
    )
    prompt = (
        f"Current roster:\n{roster_summary}\n\n"
        f"Member news this week:\n{member_news_text}\n\n"
        f"Potential new candidates:\n{new_candidate_snippets}"
    )

    response = call_gemini(system, prompt, max_tokens=2000)
    if not response:
        return None

    try:
        proposal = json.loads(_extract_json(response))
        proposal["generated_at"] = datetime.now().isoformat()
        set_review_proposal(proposal)
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] WEEKLY_REVIEW — "
            f"Gemini proposal: {proposal.get('summary', '')}"
        )
        return proposal
    except (json.JSONDecodeError, ValueError):
        logger.error("Could not parse weekly review JSON from Gemini")
        return None
