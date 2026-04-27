"""Forecast next run times for a cron job based on its expression."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from cronwrap.schedule import is_due


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def next_runs(
    cron_expr: str,
    count: int = 5,
    after: Optional[datetime] = None,
    max_search_minutes: int = 525_600,  # 1 year
) -> List[datetime]:
    """Return the next *count* datetimes when *cron_expr* is due.

    Args:
        cron_expr: A standard five-field cron expression.
        count: How many future run times to return.
        after: Start searching after this datetime (default: now).
        max_search_minutes: Safety limit to avoid infinite loops.

    Returns:
        A list of timezone-aware UTC datetimes.
    """
    if count < 1:
        raise ValueError("count must be >= 1")

    start = (after or _utcnow()).replace(second=0, microsecond=0)
    # Advance by one minute so we never return the current minute.
    candidate = start + timedelta(minutes=1)

    results: List[datetime] = []
    for _ in range(max_search_minutes):
        if is_due(cron_expr, candidate):
            results.append(candidate)
            if len(results) == count:
                break
        candidate += timedelta(minutes=1)

    return results


def forecast_summary(cron_expr: str, count: int = 5, after: Optional[datetime] = None) -> str:
    """Return a human-readable forecast string."""
    runs = next_runs(cron_expr, count=count, after=after)
    if not runs:
        return f"No upcoming runs found for '{cron_expr}'"
    lines = [f"Next {len(runs)} run(s) for '{cron_expr}':"]
    for i, dt in enumerate(runs, 1):
        lines.append(f"  {i}. {dt.strftime('%Y-%m-%d %H:%M UTC')}")
    return "\n".join(lines)
