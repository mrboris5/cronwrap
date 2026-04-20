"""Stagger support: distribute job starts across a time window to avoid thundering herd."""

import hashlib
import math
from datetime import datetime, timedelta


def _parse_seconds(value: str) -> int:
    """Parse a duration string like '30s', '5m', '2h' into seconds."""
    value = value.strip()
    if value.endswith('s'):
        return int(value[:-1])
    if value.endswith('m'):
        return int(value[:-1]) * 60
    if value.endswith('h'):
        return int(value[:-1]) * 3600
    raise ValueError(f"Invalid duration: {value!r}. Use s/m/h suffix.")


def stagger_offset(job_id: str, window: str, total_jobs: int = 1, index: int = 0) -> int:
    """Compute a deterministic stagger offset in seconds for a job.

    Uses a hash of job_id to produce a consistent offset within [0, window_seconds).
    Optionally, if total_jobs > 1 and index is provided, spreads jobs evenly.

    Args:
        job_id: Unique job identifier.
        window: Duration string for the stagger window (e.g. '10m').
        total_jobs: Total number of jobs sharing the window.
        index: Zero-based index of this job among total_jobs.

    Returns:
        Offset in seconds.
    """
    window_seconds = _parse_seconds(window)
    if total_jobs > 1:
        slot = window_seconds / total_jobs
        base = int(slot * index)
        # Add a small hash-based jitter within the slot
        digest = int(hashlib.md5(job_id.encode()).hexdigest(), 16)
        jitter = digest % max(1, int(slot))
        return base + jitter
    digest = int(hashlib.md5(job_id.encode()).hexdigest(), 16)
    return digest % window_seconds


def stagger_start(job_id: str, window: str, now: datetime | None = None,
                  total_jobs: int = 1, index: int = 0) -> datetime:
    """Return the datetime when this job should start after staggering.

    Args:
        job_id: Unique job identifier.
        window: Duration string for the stagger window.
        now: Reference time (defaults to utcnow).
        total_jobs: Total jobs in the group.
        index: Index of this job.

    Returns:
        datetime when the job should start.
    """
    if now is None:
        now = datetime.utcnow()
    offset = stagger_offset(job_id, window, total_jobs=total_jobs, index=index)
    return now + timedelta(seconds=offset)


def stagger_reason(job_id: str, window: str, total_jobs: int = 1, index: int = 0) -> str:
    """Return a human-readable explanation of the stagger delay."""
    offset = stagger_offset(job_id, window, total_jobs=total_jobs, index=index)
    minutes, seconds = divmod(offset, 60)
    if minutes:
        return f"Job '{job_id}' staggered by {minutes}m {seconds}s within {window} window."
    return f"Job '{job_id}' staggered by {seconds}s within {window} window."
