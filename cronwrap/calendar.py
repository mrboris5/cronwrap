"""Calendar-based job blocking: skip jobs on specified dates or weekdays."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

WEEKDAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _parse_date(s: str) -> date:
    """Parse YYYY-MM-DD date string."""
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        raise ValueError(f"Invalid date: {s!r} (expected YYYY-MM-DD)")


def _parse_weekday(s: str) -> int:
    """Parse weekday name to 0=Mon..6=Sun index."""
    s = s.strip().lower()
    if s not in WEEKDAY_NAMES:
        raise ValueError(f"Unknown weekday: {s!r}")
    return WEEKDAY_NAMES.index(s)


def is_blocked_date(blocked_dates: List[str], now: Optional[date] = None) -> bool:
    """Return True if today matches any blocked date."""
    today = now or date.today()
    for raw in blocked_dates:
        if _parse_date(raw) == today:
            return True
    return False


def is_blocked_weekday(blocked_weekdays: List[str], now: Optional[date] = None) -> bool:
    """Return True if today's weekday is in the blocked list."""
    today = now or date.today()
    blocked_indices = [_parse_weekday(d) for d in blocked_weekdays]
    return today.weekday() in blocked_indices


def calendar_blocked(
    blocked_dates: Optional[List[str]] = None,
    blocked_weekdays: Optional[List[str]] = None,
    now: Optional[date] = None,
) -> bool:
    """Return True if the job should be blocked based on calendar rules."""
    today = now or date.today()
    if blocked_dates and is_blocked_date(blocked_dates, today):
        return True
    if blocked_weekdays and is_blocked_weekday(blocked_weekdays, today):
        return True
    return False


def calendar_reason(
    blocked_dates: Optional[List[str]] = None,
    blocked_weekdays: Optional[List[str]] = None,
    now: Optional[date] = None,
) -> str:
    today = now or date.today()
    if blocked_dates and is_blocked_date(blocked_dates, today):
        return f"blocked date {today.isoformat()}"
    if blocked_weekdays and is_blocked_weekday(blocked_weekdays, today):
        return f"blocked weekday {WEEKDAY_NAMES[today.weekday()]}"
    return f"not blocked ({today.isoformat()})"
