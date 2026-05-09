"""Blackout window management for cronwrap.

Blackout windows prevent jobs from running during specified date/time ranges,
such as maintenance windows, holidays, or freeze periods.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def load_blackouts(path: str) -> Dict[str, List[dict]]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, ValueError):
        return {}


def save_blackouts(path: str, data: Dict[str, List[dict]]) -> None:
    Path(path).write_text(json.dumps(data, indent=2))


def add_blackout(
    path: str,
    job_id: str,
    start: str,
    end: str,
    reason: str = "",
) -> dict:
    """Add a blackout window for a job."""
    data = load_blackouts(path)
    entry = {
        "start": start,
        "end": end,
        "reason": reason,
        "created_at": _now_iso(),
    }
    data.setdefault(job_id, []).append(entry)
    save_blackouts(path, data)
    return entry


def remove_blackout(path: str, job_id: str, index: int) -> bool:
    """Remove a blackout window by index. Returns True if removed."""
    data = load_blackouts(path)
    windows = data.get(job_id, [])
    if index < 0 or index >= len(windows):
        return False
    windows.pop(index)
    data[job_id] = windows
    save_blackouts(path, data)
    return True


def get_blackouts(path: str, job_id: str) -> List[dict]:
    return load_blackouts(path).get(job_id, [])


def is_blacked_out(
    path: str,
    job_id: str,
    at: Optional[datetime] = None,
) -> bool:
    """Return True if the job is currently in a blackout window."""
    now = at or _now()
    for window in get_blackouts(path, job_id):
        try:
            start = datetime.fromisoformat(window["start"])
            end = datetime.fromisoformat(window["end"])
            if start <= now <= end:
                return True
        except (ValueError, KeyError):
            continue
    return False


def blackout_reason(
    path: str,
    job_id: str,
    at: Optional[datetime] = None,
) -> str:
    """Return a human-readable reason if blacked out, else empty string."""
    now = at or _now()
    for window in get_blackouts(path, job_id):
        try:
            start = datetime.fromisoformat(window["start"])
            end = datetime.fromisoformat(window["end"])
            if start <= now <= end:
                reason = window.get("reason", "")
                msg = f"Blacked out until {window['end']}"
                if reason:
                    msg += f" ({reason})"
                return msg
        except (ValueError, KeyError):
            continue
    return ""
