"""Deadline enforcement: block a job if it missed its allowed start window."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_seconds(value: str) -> int:
    """Parse a duration string like '30s', '5m', '2h', '1d' into seconds."""
    value = value.strip()
    match = re.fullmatch(r"(\d+)([smhd])", value)
    if not match:
        raise ValueError(f"Invalid duration: {value!r}. Expected format like '30s', '5m', '2h', '1d'.")
    amount, unit = int(match.group(1)), match.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return amount * multipliers[unit]


def is_past_deadline(
    scheduled_at: datetime,
    deadline: str,
    now: Optional[datetime] = None,
) -> bool:
    """Return True if the current time is past scheduled_at + deadline duration."""
    if now is None:
        now = _now()
    max_seconds = _parse_seconds(deadline)
    scheduled_utc = scheduled_at.astimezone(timezone.utc)
    elapsed = (now - scheduled_utc).total_seconds()
    return elapsed > max_seconds


def deadline_reason(
    job_id: str,
    scheduled_at: datetime,
    deadline: str,
    now: Optional[datetime] = None,
) -> str:
    """Return a human-readable reason string when a deadline has been missed."""
    if now is None:
        now = _now()
    max_seconds = _parse_seconds(deadline)
    scheduled_utc = scheduled_at.astimezone(timezone.utc)
    elapsed = int((now - scheduled_utc).total_seconds())
    return (
        f"Job '{job_id}' missed its deadline: scheduled at {scheduled_utc.isoformat()}, "
        f"deadline was {deadline} ({max_seconds}s), elapsed {elapsed}s."
    )


def check_deadline(
    job_id: str,
    scheduled_at: Optional[datetime],
    deadline: Optional[str],
    now: Optional[datetime] = None,
) -> tuple[bool, str]:
    """Return (blocked, reason). blocked=True means the job should not run."""
    if not deadline or scheduled_at is None:
        return False, ""
    if now is None:
        now = _now()
    if is_past_deadline(scheduled_at, deadline, now=now):
        return True, deadline_reason(job_id, scheduled_at, deadline, now=now)
    return False, ""
