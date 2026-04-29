"""Enforce quota policies against run history."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from cronwrap.quota_policy import get_quota


def _parse_period(period: str) -> timedelta:
    """Parse period strings like '1h', '24h', '7d', '30m'."""
    m = re.fullmatch(r"(\d+)([smhd])", period.strip())
    if not m:
        raise ValueError(f"Invalid period: {period!r}")
    value, unit = int(m.group(1)), m.group(2)
    return {
        "s": timedelta(seconds=value),
        "m": timedelta(minutes=value),
        "h": timedelta(hours=value),
        "d": timedelta(days=value),
    }[unit]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def runs_in_period(history: List[dict], period: str) -> int:
    """Count history entries within the given period."""
    delta = _parse_period(period)
    cutoff = _utcnow() - delta
    count = 0
    for entry in history:
        ts = entry.get("timestamp") or entry.get("started_at") or ""
        try:
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                count += 1
        except (ValueError, TypeError):
            continue
    return count


def is_quota_exceeded(
    job_id: str,
    history: List[dict],
    policy_path: Optional[str] = None,
) -> bool:
    """Return True if the job has exceeded its quota."""
    kwargs = {"path": policy_path} if policy_path else {}
    entry = get_quota(job_id, **kwargs)
    if entry is None:
        return False
    count = runs_in_period(history, entry["period"])
    return count >= entry["max_runs"]


def quota_exceeded_reason(
    job_id: str,
    history: List[dict],
    policy_path: Optional[str] = None,
) -> str:
    """Human-readable reason if quota is exceeded, else empty string."""
    kwargs = {"path": policy_path} if policy_path else {}
    entry = get_quota(job_id, **kwargs)
    if entry is None:
        return ""
    count = runs_in_period(history, entry["period"])
    if count >= entry["max_runs"]:
        return (
            f"Quota exceeded for '{job_id}': "
            f"{count}/{entry['max_runs']} runs in last {entry['period']}."
        )
    return ""
