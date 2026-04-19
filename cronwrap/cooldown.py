"""Cooldown: prevent a job from running too soon after its last run."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from cronwrap.history import last_runs


def _parse_seconds(duration: str) -> int:
    """Parse a duration string like '30s', '5m', '2h' into seconds."""
    duration = duration.strip()
    if duration.endswith("s"):
        return int(duration[:-1])
    if duration.endswith("m"):
        return int(duration[:-1]) * 60
    if duration.endswith("h"):
        return int(duration[:-1]) * 3600
    if duration.endswith("d"):
        return int(duration[:-1]) * 86400
    raise ValueError(f"Cannot parse duration: {duration!r}")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def is_cooling_down(
    job_id: str,
    cooldown: str,
    history_file: str,
    *,
    only_on_success: bool = False,
) -> bool:
    """Return True if the job is still within its cooldown period."""
    seconds = _parse_seconds(cooldown)
    runs = last_runs(job_id, history_file, n=1)
    if not runs:
        return False
    last = runs[0]
    if only_on_success and not last.get("success", False):
        return False
    finished_at = last.get("finished_at") or last.get("started_at")
    if not finished_at:
        return False
    last_dt = datetime.fromisoformat(finished_at)
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)
    elapsed = (_now() - last_dt).total_seconds()
    return elapsed < seconds


def cooldown_reason(
    job_id: str,
    cooldown: str,
    history_file: str,
    *,
    only_on_success: bool = False,
) -> Optional[str]:
    """Return a human-readable reason string if cooling down, else None."""
    if is_cooling_down(job_id, cooldown, history_file, only_on_success=only_on_success):
        return f"Job '{job_id}' is within cooldown period of {cooldown}"
    return None
