"""Watchdog module: tracks expected job heartbeats and detects missed runs."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

_DEFAULT_MAX = 500


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load_watchdog(path: str) -> dict:
    """Load watchdog state from a JSON file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_watchdog(path: str, state: dict) -> None:
    """Persist watchdog state to a JSON file."""
    Path(path).write_text(json.dumps(state, indent=2))


def register_watchdog(path: str, job_id: str, interval: str, grace: str = "5m") -> dict:
    """Register a job with an expected run interval and grace period."""
    state = load_watchdog(path)
    state[job_id] = {
        "interval": interval,
        "grace": grace,
        "last_seen": None,
        "registered_at": _now_iso(),
    }
    save_watchdog(path, state)
    return state[job_id]


def checkin(path: str, job_id: str) -> dict:
    """Record a successful check-in for a job."""
    state = load_watchdog(path)
    if job_id not in state:
        state[job_id] = {"interval": None, "grace": "5m", "registered_at": _now_iso()}
    state[job_id]["last_seen"] = _now_iso()
    save_watchdog(path, state)
    return state[job_id]


def _parse_seconds(duration: str) -> int:
    """Parse a duration string like '5m', '2h', '30s' into seconds."""
    duration = duration.strip()
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if duration[-1] in units:
        return int(duration[:-1]) * units[duration[-1]]
    return int(duration)


def is_overdue(path: str, job_id: str) -> bool:
    """Return True if the job has not checked in within interval + grace."""
    state = load_watchdog(path)
    entry = state.get(job_id)
    if not entry or not entry.get("interval") or not entry.get("last_seen"):
        return False
    interval_s = _parse_seconds(entry["interval"])
    grace_s = _parse_seconds(entry.get("grace", "0s"))
    deadline = datetime.fromisoformat(entry["last_seen"]) + timedelta(seconds=interval_s + grace_s)
    return _now() > deadline


def overdue_reason(path: str, job_id: str) -> Optional[str]:
    """Return a human-readable reason if the job is overdue, else None."""
    if not is_overdue(path, job_id):
        return None
    state = load_watchdog(path)
    entry = state[job_id]
    return (
        f"Job '{job_id}' last seen at {entry['last_seen']} — "
        f"expected every {entry['interval']} (grace {entry.get('grace', '0s')})"
    )
