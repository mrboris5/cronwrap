"""Reminder module: schedule one-off reminders tied to job IDs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_MAX_ENTRIES = 200


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_reminders(path: str) -> dict[str, list[dict[str, Any]]]:
    """Load reminders from *path*; return empty dict on missing/corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_reminders(path: str, data: dict[str, list[dict[str, Any]]]) -> None:
    """Persist *data* to *path*, trimming each job list to _MAX_ENTRIES."""
    trimmed = {k: v[-_MAX_ENTRIES:] for k, v in data.items()}
    Path(path).write_text(json.dumps(trimmed, indent=2))


def add_reminder(
    path: str,
    job_id: str,
    message: str,
    remind_at: str,
) -> dict[str, Any]:
    """Add a reminder for *job_id* that fires at *remind_at* (ISO timestamp)."""
    data = load_reminders(path)
    entry: dict[str, Any] = {
        "job_id": job_id,
        "message": message,
        "remind_at": remind_at,
        "created_at": _now_iso(),
        "acknowledged": False,
    }
    data.setdefault(job_id, []).append(entry)
    save_reminders(path, data)
    return entry


def acknowledge_reminder(path: str, job_id: str, index: int) -> bool:
    """Mark reminder at *index* for *job_id* as acknowledged. Returns True on success."""
    data = load_reminders(path)
    entries = data.get(job_id, [])
    if index < 0 or index >= len(entries):
        return False
    entries[index]["acknowledged"] = True
    entries[index]["acknowledged_at"] = _now_iso()
    save_reminders(path, data)
    return True


def get_reminders(
    path: str,
    job_id: str,
    pending_only: bool = False,
) -> list[dict[str, Any]]:
    """Return reminders for *job_id*, optionally filtering to unacknowledged ones."""
    data = load_reminders(path)
    entries = data.get(job_id, [])
    if pending_only:
        return [e for e in entries if not e.get("acknowledged", False)]
    return list(entries)


def due_reminders(path: str) -> list[dict[str, Any]]:
    """Return all unacknowledged reminders whose remind_at <= now."""
    now = datetime.now(timezone.utc).isoformat()
    data = load_reminders(path)
    result = []
    for entries in data.values():
        for entry in entries:
            if not entry.get("acknowledged") and entry.get("remind_at", "") <= now:
                result.append(entry)
    return result
