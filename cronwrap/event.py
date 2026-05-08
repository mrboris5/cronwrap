"""Event log: record and query named events for jobs."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

MAX_EVENTS = 500


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_events(path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load event log from *path*; return empty dict on missing/corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_events(
    data: Dict[str, List[Dict[str, Any]]], path: str, max_entries: int = MAX_EVENTS
) -> None:
    """Persist event log, trimming each job's list to *max_entries*."""
    for job_id in data:
        data[job_id] = data[job_id][-max_entries:]
    Path(path).write_text(json.dumps(data, indent=2))


def record_event(
    job_id: str,
    event_type: str,
    message: str,
    path: str,
    extra: Optional[Dict[str, Any]] = None,
    max_entries: int = MAX_EVENTS,
) -> Dict[str, Any]:
    """Append an event for *job_id* and return the new entry."""
    data = load_events(path)
    entry: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "event_type": event_type,
        "message": message,
    }
    if extra:
        entry.update(extra)
    data.setdefault(job_id, []).append(entry)
    save_events(data, path, max_entries)
    return entry


def get_events(
    job_id: str,
    path: str,
    event_type: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Return recent events for *job_id*, optionally filtered by *event_type*."""
    data = load_events(path)
    entries = data.get(job_id, [])
    if event_type is not None:
        entries = [e for e in entries if e.get("event_type") == event_type]
    return entries[-limit:]


def clear_events(job_id: str, path: str) -> int:
    """Remove all events for *job_id*; return count removed."""
    data = load_events(path)
    removed = len(data.pop(job_id, []))
    if removed:
        save_events(data, path)
    return removed
