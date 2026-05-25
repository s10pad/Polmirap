"""
Roster Discovery Engine — finds the top 10 successful US investors across all fields.
Each member is tagged by data source which decides if they can be auto-mirrored:
  politician   → stock_act  → mirrorable  (~30-45 day lag)
  fund_manager → 13f        → mirrorable  (quarterly +45d)
  insider      → form4      → mirrorable  (~2 day lag)
  athlete/celebrity → news  → watch-only

Runs on first boot (empty roster) and weekly via Sunday scheduler job.
Changes are auto-applied — no approval gate (operator decision).
"""
import json
import logging
from datetime import datetime

from fetcher import fetch_roster_candidates, fetch_edgar_13f_filers, fetch_edgar_form4_insiders
from agent import call_gemini, _extract_json
from roster import get_active_members, add_member, remove_member
from memory import get_roster, append_changelog, is_roster_initialized

logger = logging.getLogger(__name__)

_SOURCE_META = {
    "politician":    {"data_source": "stock_act", "mirrorable": True,  "filing_latency": "~30-45 days"},
    "fund_manager":  {"data_source": "13f",        "mirrorable": True,  "filing_latency": "quarterly +45d"},
    "insider":       {"data_source": "form4",       "mirrorable": True,  "filing_latency": "~2 days"},
    "athlete":       {"data_source": "news",        "mirrorable": False, "filing_latency": "watch-only"},
    "celebrity":     {"data_source": "news",        "mirrorable": False, "filing_latency": "watch-only"},
    "public_figure": {"data_source": "news",        "mirrorable": False, "filing_latency": "watch-only"},
}


def _enrich(member: dict) -> dict:
    """Add data_source, mirrorable, filing_latency, last_verified from category."""
    meta = _SOURCE_META.get(member.get("category", "public_figure"), _SOURCE_META["public_figure"])
    return {**member, **meta, "last_verified": datetime.now().isoformat()}


def _rank_with_gemini(all_results: list) -> list:
    """Call Gemini to rank top 10 investors from multi-source search results."""
    snippets = "\n".join(
        f"- {r.get('title', '')}: {r.get('description', '')}"
        for r in all_results[:60]
    )
    system = (
        "You are building a roster of the top 10 successful US investors to mirror in a stock trading system. "
        "Rank by: (1) documented disclosure track record from public filings, (2) news reputation, "
        "(3) AI analysis of their investment thesis and consistency. "
        "Include diverse fields: politicians (STOCK Act filers), fund managers (13F filers), "
        "corporate insiders/CEOs (Form 4 filers), athletes/celebrities (news-only, watch-only). "
        "Prioritize filers who have verifiable disclosed trades over non-filers. "
        "Return ONLY a JSON array of exactly 10 objects — no prose, no fences:\n"
        '[{"name": str, "category": "politician"|"fund_manager"|"insider"|"athlete"|"celebrity", '
        '"why_added": "2-3 sentences with evidence of track record", '
        '"weight": float 0.8-1.5, "rank": int 1-10}]'
    )
    response = call_gemini(system, f"Multi-source data about successful US investors:\n{snippets}", max_tokens=3000)
    if not response:
        return []
    try:
        candidates = json.loads(_extract_json(response))
        return candidates[:10] if isinstance(candidates, list) else []
    except Exception as e:
        logger.error(f"Discovery: could not parse Gemini response: {e}")
        return []


def discover_and_refresh_roster() -> tuple[int, list]:
    """
    Full discovery run: gather multi-source data → rank with Gemini → update roster.
    Returns (changes_count, list of change descriptions).
    Auto-applies all changes immediately.
    """
    logger.info("Roster discovery: gathering data from Brave + SEC EDGAR")

    brave_results = fetch_roster_candidates()
    edgar_13f = fetch_edgar_13f_filers(count=15)
    edgar_form4 = fetch_edgar_form4_insiders(count=15)
    all_results = brave_results + edgar_13f + edgar_form4

    logger.info(
        f"Discovery: {len(brave_results)} Brave + {len(edgar_13f)} 13F + {len(edgar_form4)} Form4 results"
    )

    candidates = _rank_with_gemini(all_results)
    if not candidates:
        logger.error("Discovery: Gemini returned no candidates")
        return 0, []

    enriched = [_enrich(c) for c in candidates]

    if not is_roster_initialized():
        count = 0
        for m in enriched:
            m.setdefault("added_date", datetime.now().strftime("%Y-%m-%d"))
            m.setdefault("performance_since_added", 0.0)
            m.setdefault("status", "active")
            if add_member(m):
                count += 1
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] DISCOVERY INIT — "
            f"Bootstrapped {count} members via multi-source AI discovery."
        )
        logger.info(f"Discovery: bootstrapped {count} members")
        return count, [f"Added {m['name']} ({m['category']})" for m in enriched[:count]]

    current = {m["name"].lower(): m for m in get_active_members()}
    new_names = {c["name"].lower() for c in enriched}
    changes = []

    for name_lower, member in list(current.items()):
        if name_lower not in new_names:
            reason = "Not ranked in top 10 on weekly roster refresh"
            if remove_member(member["name"], reason):
                changes.append(f"Removed {member['name']}: {reason}")

    active_names = {m["name"].lower() for m in get_active_members()}
    for candidate in enriched:
        if candidate["name"].lower() not in active_names:
            candidate.setdefault("added_date", datetime.now().strftime("%Y-%m-%d"))
            candidate.setdefault("performance_since_added", 0.0)
            candidate.setdefault("status", "active")
            if add_member(candidate):
                changes.append(f"Added {candidate['name']} ({candidate['category']})")

    if changes:
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] DISCOVERY REFRESH — "
            f"{len(changes)} change(s): {'; '.join(changes)}"
        )
    else:
        append_changelog(
            f"[{datetime.now().strftime('%Y-%m-%d')}] DISCOVERY REFRESH — Roster stable, no changes."
        )

    logger.info(f"Discovery refresh complete: {len(changes)} change(s)")
    return len(changes), changes
