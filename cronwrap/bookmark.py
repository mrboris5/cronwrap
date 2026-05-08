"""Job bookmark module — save and retrieve named execution points."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_DEFAULT_MAX = 200


def load_bookmarks(path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load bookmarks from *path*; return empty dict on missing/corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_bookmarks(
    data: Dict[str, List[Dict[str, Any]]],
    path: str,
    max_entries: int = _DEFAULT_MAX,
) -> None:
    """Persist *data* to *path*, trimming each job list to *max_entries*."""
    trimmed = {job: entries[-max_entries:] for job, entries in data.items()}
    Path(path).write_text(json.dumps(trimmed, indent=2))


def add_bookmark(
    job_id: str,
    name: str,
    value: str,
    path: str,
    *,
    max_entries: int = _DEFAULT_MAX,
) -> Dict[str, Any]:
    """Add a named bookmark *name* with *value* for *job_id*."""
    data = load_bookmarks(path)
    entry: Dict[str, Any] = {"name": name, "value": value}
    data.setdefault(job_id, []).append(entry)
    save_bookmarks(data, path, max_entries=max_entries)
    return entry


def get_bookmark(job_id: str, name: str, path: str) -> Optional[str]:
    """Return the value of the most recent bookmark *name* for *job_id*, or None."""
    data = load_bookmarks(path)
    entries = data.get(job_id, [])
    for entry in reversed(entries):
        if entry.get("name") == name:
            return entry.get("value")
    return None


def remove_bookmark(job_id: str, name: str, path: str) -> bool:
    """Remove all bookmarks named *name* for *job_id*. Return True if any removed."""
    data = load_bookmarks(path)
    before = data.get(job_id, [])
    after = [e for e in before if e.get("name") != name]
    if len(after) == len(before):
        return False
    data[job_id] = after
    save_bookmarks(data, path)
    return True


def list_bookmarks(job_id: str, path: str) -> List[Dict[str, Any]]:
    """Return all bookmark entries for *job_id*."""
    return load_bookmarks(path).get(job_id, [])
