"""
Roster management — handles member list, weekly review proposals, and approval workflow.
"""

import logging
from datetime import datetime
from typing import Optional
from memory import (
    get_roster, set_roster, get_review_proposal, set_review_proposal,
    clear_review_proposal, append_changelog, is_roster_initialized,
    set_last_roster_boot,
)

logger = logging.getLogger(__name__)

MAX_ROSTER_SIZE = 10
MAX_WEEKLY_CHANGES = 3


def get_active_members() -> list:
    """Return only active (not pending removal) roster members."""
    return [m for m in get_roster() if m.get("status") == "active"]


def find_member(name: str) -> Optional[dict]:
    """Find a roster member by name (case-insensitive). Returns None if not found."""
    roster = get_roster()
    name_lower = name.lower()
    for m in roster:
        if m["name"].lower() == name_lower:
            return m
    return None


def add_member(member: dict) -> bool:
    """
    Add a new person to the roster. Validates required fields.
    member dict must have: name, category, why_added, weight.
    """
    required = {"name", "category", "why_added", "weight"}
    if not required.issubset(member.keys()):
        logger.error(f"Member missing fields: {required - member.keys()}")
        return False

    roster = get_roster()
    if len([m for m in roster if m.get("status") == "active"]) >= MAX_ROSTER_SIZE:
        logger.warning("Roster full — cannot add without removing someone first")
        return False

    if find_member(member["name"]):
        logger.warning(f"{member['name']} already on roster")
        return False

    member.setdefault("added_date", datetime.now().strftime("%Y-%m-%d"))
    member.setdefault("performance_since_added", 0.0)
    member.setdefault("last_reviewed", datetime.now().strftime("%Y-%m-%d"))
    member.setdefault("status", "active")

    roster.append(member)
    set_roster(roster)
    append_changelog(
        f"[{datetime.now().strftime('%Y-%m-%d')}] ROSTER ADD {member['name']} — "
        f"Added to roster. Reason: {member['why_added']}"
    )
    return True


def remove_member(name: str, reason: str) -> bool:
    """Remove a roster member by name. Logs the reason."""
    roster = get_roster()
    updated = []
    removed = False
    for m in roster:
        if m["name"].lower() == name.lower():
            removed = True
            append_changelog(
                f"[{datetime.now().strftime('%Y-%m-%d')}] ROSTER REMOVE {name} — {reason}"
            )
        else:
            updated.append(m)
    if removed:
        set_roster(updated)
    return removed


def update_member_weight(name: str, new_weight: float) -> bool:
    """Update a roster member's conviction weight. Logs the change."""
    roster = get_roster()
    for m in roster:
        if m["name"].lower() == name.lower():
            old_weight = m.get("weight", 1.0)
            m["weight"] = new_weight
            set_roster(roster)
            append_changelog(
                f"[{datetime.now().strftime('%Y-%m-%d')}] WEIGHT UPDATE {name} — "
                f"Weight changed from {old_weight} to {new_weight}"
            )
            return True
    return False


def update_member_performance(name: str, performance_pct: float) -> bool:
    """Update the performance_since_added field for a roster member."""
    roster = get_roster()
    for m in roster:
        if m["name"].lower() == name.lower():
            m["performance_since_added"] = round(performance_pct, 4)
            m["last_reviewed"] = datetime.now().strftime("%Y-%m-%d")
            set_roster(roster)
            return True
    return False


def apply_review_proposal(proposal: dict) -> tuple[int, list]:
    """
    Apply an approved weekly review proposal. Max 3 changes.
    Returns (changes_applied, list of action descriptions).
    """
    changes = proposal.get("changes", [])[:MAX_WEEKLY_CHANGES]
    applied = []

    for change in changes:
        action = change.get("action")
        name = change.get("name")
        reason = change.get("reason", "No reason given")

        if action == "remove":
            if remove_member(name, reason):
                applied.append(f"Removed {name}: {reason}")

        elif action == "add":
            new_member = {
                "name": name,
                "category": change.get("category", "public_figure"),
                "why_added": reason,
                "weight": change.get("suggested_weight", 1.0),
            }
            if add_member(new_member):
                applied.append(f"Added {name}: {reason}")

        elif action == "weight_update":
            new_w = change.get("suggested_weight", 1.0)
            if update_member_weight(name, new_w):
                applied.append(f"Updated weight for {name} to {new_w}: {reason}")

    clear_review_proposal()
    return len(applied), applied


def bootstrap_roster(ai_candidates: list) -> bool:
    """
    Initialize the roster from AI-discovered candidates on first run.
    ai_candidates: list of member dicts from agent.discover_initial_roster().
    """
    if is_roster_initialized():
        logger.info("Roster already initialized — skipping bootstrap")
        return False

    count = 0
    for candidate in ai_candidates[:MAX_ROSTER_SIZE]:
        if add_member(candidate):
            count += 1

    ts = datetime.now().isoformat()
    set_last_roster_boot(ts)
    append_changelog(
        f"[{datetime.now().strftime('%Y-%m-%d')}] SYSTEM INIT — "
        f"Roster bootstrapped with {count} members via AI discovery."
    )
    logger.info(f"Roster bootstrapped with {count} members")
    return count > 0
