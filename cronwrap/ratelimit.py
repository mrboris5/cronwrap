"""Rate limiting: cap how many times a job can run in a time window."""

from __future__ import annotations

import time
from typing import List

from cronwrap.history import load_history, HistoryEntry


def _parse_window(window: str) -> int:
    """Parse a window string like '1h', '30m', '3600s' into seconds."""
    window = window.strip()
    if window.endswith('d'):
        return int(window[:-1]) * 86400
    if window.endswith('h'):
        return int(window[:-1]) * 3600
    if window.endswith('m'):
        return int(window[:-1]) * 60
    if window.endswith('s'):
        return int(window[:-1])
    raise ValueError(f"Invalid window format: {window!r}")


def runs_in_window(history_file: str, job_id: str, window: str) -> List[dict]:
    """Return runs for job_id that occurred within the given time window."""
    seconds = _parse_window(window)
    cutoff = time.time() - seconds
    entries = load_history(history_file, job_id)
    result = []
    for e in entries:
        try:
            ts = time.mktime(time.strptime(e["started_at"], "%Y-%m-%dT%H:%M:%S"))
        except (KeyError, ValueError):
            continue
        if ts >= cutoff:
            result.append(e)
    return result


def is_rate_limited(history_file: str, job_id: str, max_runs: int, window: str) -> bool:
    """Return True if job has reached max_runs within the window."""
    recent = runs_in_window(history_file, job_id, window)
    return len(recent) >= max_runs


def rate_limit_reason(history_file: str, job_id: str, max_runs: int, window: str) -> str:
    """Return a human-readable reason string for rate limiting."""
    recent = runs_in_window(history_file, job_id, window)
    return (
        f"Job '{job_id}' has run {len(recent)} time(s) in the last {window} "
        f"(limit: {max_runs})"
    )
