"""Manual and event-based job trigger tracking."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_MAX_ENTRIES = 200


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_triggers(path: str) -> List[Dict[str, Any]]:
    """Load trigger records from a JSON file."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, ValueError):
        return []


def save_triggers(path: str, entries: List[Dict[str, Any]], max_entries: int = _MAX_ENTRIES) -> None:
    """Persist trigger records, trimming to max_entries."""
    trimmed = entries[-max_entries:]
    with open(path, "w") as fh:
        json.dump(trimmed, fh, indent=2)


def record_trigger(
    path: str,
    job_id: str,
    trigger_type: str,
    source: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a trigger event for a job."""
    entries = load_triggers(path)
    entry: Dict[str, Any] = {
        "job_id": job_id,
        "trigger_type": trigger_type,
        "source": source or "manual",
        "reason": reason or "",
        "triggered_at": _now_iso(),
        "acknowledged": False,
    }
    entries.append(entry)
    save_triggers(path, entries)
    return entry


def acknowledge_trigger(path: str, job_id: str) -> bool:
    """Mark the latest unacknowledged trigger for a job as acknowledged."""
    entries = load_triggers(path)
    for entry in reversed(entries):
        if entry.get("job_id") == job_id and not entry.get("acknowledged"):
            entry["acknowledged"] = True
            save_triggers(path, entries)
            return True
    return False


def pending_triggers(path: str, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return unacknowledged triggers, optionally filtered by job_id."""
    entries = load_triggers(path)
    return [
        e for e in entries
        if not e.get("acknowledged")
        and (job_id is None or e.get("job_id") == job_id)
    ]


def last_trigger(path: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Return the most recent trigger entry for a job."""
    entries = load_triggers(path)
    for entry in reversed(entries):
        if entry.get("job_id") == job_id:
            return entry
    return None
