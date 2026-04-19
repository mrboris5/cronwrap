"""Random jitter helpers to spread cron job execution."""
import random
import time
from typing import Optional


def _parse_seconds(value: str) -> float:
    """Parse a duration string like '30s', '2m', '1h' into seconds."""
    value = value.strip()
    if value.endswith('s'):
        return float(value[:-1])
    if value.endswith('m'):
        return float(value[:-1]) * 60
    if value.endswith('h'):
        return float(value[:-1]) * 3600
    raise ValueError(f"Invalid duration: {value!r}. Use s/m/h suffix.")


def jitter_seconds(max_jitter: str) -> float:
    """Return a random float in [0, max_jitter_seconds]."""
    limit = _parse_seconds(max_jitter)
    if limit < 0:
        raise ValueError("max_jitter must be non-negative")
    return random.uniform(0, limit)


def apply_jitter(max_jitter: str, dry_run: bool = False) -> float:
    """Sleep for a random duration up to max_jitter. Returns seconds slept."""
    delay = jitter_seconds(max_jitter)
    if not dry_run:
        time.sleep(delay)
    return delay


def jitter_reason(max_jitter: str, slept: Optional[float] = None) -> str:
    """Return a human-readable description of the jitter applied."""
    limit = _parse_seconds(max_jitter)
    if slept is None:
        return f"Jitter up to {limit:.1f}s may be applied before execution."
    return f"Jitter applied: slept {slept:.2f}s (max {limit:.1f}s)."
