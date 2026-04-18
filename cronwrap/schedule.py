"""Schedule checking utilities for cronwrap."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


CRON_FIELDS = ("minute", "hour", "day", "month", "weekday")


def _match_field(value: int, expr: str, min_val: int, max_val: int) -> bool:
    """Return True if value matches a single cron field expression."""
    if expr == "*":
        return True
    if re.fullmatch(r"\d+", expr):
        return value == int(expr)
    m = re.fullmatch(r"\*/(\d+)", expr)
    if m:
        step = int(m.group(1))
        return (value - min_val) % step == 0
    m = re.fullmatch(r"(\d+)-(\d+)", expr)
    if m:
        return int(m.group(1)) <= value <= int(m.group(2))
    if "," in expr:
        return any(_match_field(value, part.strip(), min_val, max_val) for part in expr.split(","))
    return False


def is_due(cron_expr: str, at: Optional[datetime] = None) -> bool:
    """Return True if the cron expression matches the given datetime (default: now)."""
    if at is None:
        at = datetime.now()
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {cron_expr!r}")
    minute, hour, day, month, weekday = parts
    return (
        _match_field(at.minute, minute, 0, 59)
        and _match_field(at.hour, hour, 0, 23)
        and _match_field(at.day, day, 1, 31)
        and _match_field(at.month, month, 1, 12)
        and _match_field(at.weekday(), weekday, 0, 6)
    )


def describe(cron_expr: str) -> str:
    """Return a human-readable description of a cron expression."""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {cron_expr!r}")
    return "schedule({})".format(", ".join(f"{f}={v}" for f, v in zip(CRON_FIELDS, parts)))
