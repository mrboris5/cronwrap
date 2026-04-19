"""Time window checks: only allow jobs to run within specified time windows."""

from __future__ import annotations

import re
from datetime import datetime, time
from typing import Optional


def _parse_time(s: str) -> time:
    """Parse HH:MM time string."""
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", s.strip())
    if not m:
        raise ValueError(f"Invalid time format: {s!r} (expected HH:MM)")
    hour, minute = int(m.group(1)), int(m.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Time out of range: {s!r}")
    return time(hour, minute)


def parse_window(window: str) -> tuple[time, time]:
    """Parse 'HH:MM-HH:MM' window string into (start, end) times."""
    parts = window.split("-", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid window format: {window!r} (expected HH:MM-HH:MM)")
    return _parse_time(parts[0]), _parse_time(parts[1])


def in_window(window: str, now: Optional[datetime] = None) -> bool:
    """Return True if current time falls within the given window string."""
    if now is None:
        now = datetime.now()
    start, end = parse_window(window)
    current = now.time().replace(second=0, microsecond=0)
    if start <= end:
        return start <= current <= end
    # Overnight window e.g. 22:00-06:00
    return current >= start or current <= end


def window_reason(window: str, now: Optional[datetime] = None) -> str:
    """Return human-readable reason string for window check."""
    if now is None:
        now = datetime.now()
    start, end = parse_window(window)
    current = now.strftime("%H:%M")
    if in_window(window, now):
        return f"within window {window} (current {current})"
    return f"outside window {window} (current {current})"
