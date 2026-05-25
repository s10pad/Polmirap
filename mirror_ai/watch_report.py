"""
Weekly watch report — generates roster churn analysis and auto-applies changes.
Wraps agent.run_weekly_review() with auto-apply + Firestore storage.
Auto-apply is the operator decision (no approval gate).
"""
import logging
from datetime import datetime
from typing import Optional

from memory import get_key, set_key, append_changelog, get_roster
from agent import run_weekly_review
from roster import apply_review_proposal

logger = logging.getLogger(__name__)

_REPORT_KEY = "watch_report"


def generate_and_apply_watch_report() -> Optional[dict]:
    """
    Run weekly roster review, auto-apply all proposed changes, store the report.
    Called by the scheduler every Monday at 6am ET.
    """
    logger.info("Watch report: generating weekly review")
    proposal = run_weekly_review()
    if not proposal:
        logger.error("Watch report: no proposal returned from agent")
        return None

    count, applied = apply_review_proposal(proposal)

    report = {
        "generated_at": proposal.get("generated_at", datetime.now().isoformat()),
        "summary": proposal.get("summary", ""),
        "changes_proposed": proposal.get("changes", []),
        "changes_applied": applied,
        "changes_count": count,
        "roster_size": len([m for m in get_roster() if m.get("status") == "active"]),
    }

    set_key(_REPORT_KEY, report)
    append_changelog(
        f"[{datetime.now().strftime('%Y-%m-%d')}] WATCH_REPORT — "
        f"Auto-applied {count} change(s). {report['summary']}"
    )
    logger.info(f"Watch report complete: {count} change(s) applied")
    return report


def get_latest_watch_report() -> Optional[dict]:
    """Return the most recent stored watch report, or None if none generated yet."""
    return get_key(_REPORT_KEY)
