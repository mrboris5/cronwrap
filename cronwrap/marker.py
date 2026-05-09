"""Job marker module: attach named markers (milestones) to job runs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_MAX_ENTRIES = 500


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_markers(path: str) -> dict[str, list[dict[str, Any]]]:
    """Load markers from *path*; return empty dict on missing/corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_markers(path: str, data: dict[str, list[dict[str, Any]]]) -> None:
    """Persist markers to *path*, trimming each job list to _MAX_ENTRIES."""
    trimmed = {k: v[-_MAX_ENTRIES:] for k, v in data.items()}
    Path(path).write_text(json.dumps(trimmed, indent=2))


def add_marker(
    path: str,
    job_id: str,
    name: str,
    *,
    note: str = "",
) -> dict[str, Any]:
    """Append a named marker for *job_id* and return the new entry."""
    data = load_markers(path)
    entry: dict[str, Any] = {
        "job_id": job_id,
        "name": name,
        "note": note,
        "timestamp": _now_iso(),
    }
    data.setdefault(job_id, []).append(entry)
    save_markers(path, data)
    return entry


def get_markers(path: str, job_id: str) -> list[dict[str, Any]]:
    """Return all markers for *job_id*, newest first."""
    data = load_markers(path)
    return list(reversed(data.get(job_id, [])))


def remove_marker(path: str, job_id: str, name: str) -> int:
    """Remove all markers with *name* for *job_id*. Return count removed."""
    data = load_markers(path)
    original = data.get(job_id, [])
    kept = [e for e in original if e["name"] != name]
    removed = len(original) - len(kept)
    if removed:
        data[job_id] = kept
        save_markers(path, data)
    return removed


def clear_markers(path: str, job_id: str) -> None:
    """Remove every marker for *job_id*."""
    data = load_markers(path)
    data.pop(job_id, None)
    save_markers(path, data)
