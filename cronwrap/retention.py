"""Retention policy: prune old history/audit entries by age or count."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any


def _parse_days(value: str) -> int:
    """Parse a duration string like '7d', '30d' into integer days."""
    value = value.strip()
    if value.endswith('d'):
        try:
            return int(value[:-1])
        except ValueError:
            pass
    raise ValueError(f"Invalid retention duration: {value!r}. Expected format: '7d'")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def prune_by_age(entries: List[Dict[str, Any]], max_age: str, key: str = "timestamp") -> List[Dict[str, Any]]:
    """Return entries newer than max_age (e.g. '30d')."""
    days = _parse_days(max_age)
    cutoff = _now() - timedelta(days=days)
    result = []
    for entry in entries:
        ts_str = entry.get(key, "")
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                result.append(entry)
        except (ValueError, TypeError):
            result.append(entry)  # keep entries with unparseable timestamps
    return result


def prune_by_count(entries: List[Dict[str, Any]], max_count: int) -> List[Dict[str, Any]]:
    """Return the most recent max_count entries (assumes list is ordered oldest-first)."""
    if max_count <= 0:
        raise ValueError("max_count must be a positive integer")
    return entries[-max_count:]


def apply_retention(
    entries: List[Dict[str, Any]],
    max_age: str | None = None,
    max_count: int | None = None,
    key: str = "timestamp",
) -> List[Dict[str, Any]]:
    """Apply age and/or count retention policies to a list of entries."""
    if max_age is not None:
        entries = prune_by_age(entries, max_age, key=key)
    if max_count is not None:
        entries = prune_by_count(entries, max_count)
    return entries
