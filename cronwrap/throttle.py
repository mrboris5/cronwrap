"""Throttle / minimum-interval enforcement for cronwrap jobs."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from cronwrap.history import last_runs


def _parse_duration(s: str) -> timedelta:
    """Parse a duration string like '5m', '2h', '30s' into a timedelta."""
    s = s.strip()
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if s[-1] in units:
        return timedelta(seconds=int(s[:-1]) * units[s[-1]])
    raise ValueError(f"Unknown duration format: {s!r}")


def should_throttle(job_id: str, min_interval: str, history_file: str) -> bool:
    """
    Return True if the job ran too recently and should be skipped.

    Parameters
    ----------
    job_id:        identifier for the job (used to look up history)
    min_interval:  minimum time between runs, e.g. '10m', '1h'
    history_file:  path to the JSON history file
    """
    interval = _parse_duration(min_interval)
    runs: List[dict] = last_runs(history_file, job_id, n=1)
    if not runs:
        return False
    last_ts_str: Optional[str] = runs[0].get("started_at")
    if not last_ts_str:
        return False
    last_ts = datetime.fromisoformat(last_ts_str)
    return (datetime.utcnow() - last_ts) < interval


def throttle_reason(job_id: str, min_interval: str, history_file: str) -> str:
    """Return a human-readable reason string when throttling applies."""
    runs = last_runs(history_file, job_id, n=1)
    if not runs:
        return "no previous run found"
    last_ts_str = runs[0].get("started_at", "unknown")
    return (
        f"job '{job_id}' last ran at {last_ts_str}; "
        f"minimum interval is {min_interval}"
    )
