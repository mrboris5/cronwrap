"""Tombstone records for permanently retired/deleted jobs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PATH = ".cronwrap/tombstones.json"
MAX_ENTRIES = 500


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_tombstones(path: str = DEFAULT_PATH) -> dict[str, Any]:
    """Load tombstone records from disk."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_tombstones(records: dict[str, Any], path: str = DEFAULT_PATH) -> None:
    """Persist tombstone records to disk."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(records, indent=2))


def bury_job(
    job_id: str,
    reason: str = "",
    path: str = DEFAULT_PATH,
) -> dict[str, Any]:
    """Mark a job as permanently retired."""
    records = load_tombstones(path)
    entry: dict[str, Any] = {
        "job_id": job_id,
        "buried_at": _now_iso(),
        "reason": reason,
    }
    records[job_id] = entry
    save_tombstones(records, path)
    return entry


def is_buried(job_id: str, path: str = DEFAULT_PATH) -> bool:
    """Return True if the job has a tombstone record."""
    records = load_tombstones(path)
    return job_id in records


def get_tombstone(job_id: str, path: str = DEFAULT_PATH) -> dict[str, Any] | None:
    """Retrieve the tombstone entry for a job, or None if not buried."""
    records = load_tombstones(path)
    return records.get(job_id)


def remove_tombstone(job_id: str, path: str = DEFAULT_PATH) -> bool:
    """Remove a tombstone, allowing the job to run again. Returns True if removed."""
    records = load_tombstones(path)
    if job_id not in records:
        return False
    del records[job_id]
    save_tombstones(records, path)
    return True


def all_tombstones(path: str = DEFAULT_PATH) -> list[dict[str, Any]]:
    """Return all tombstone entries sorted by buried_at descending."""
    records = load_tombstones(path)
    entries = list(records.values())
    entries.sort(key=lambda e: e.get("buried_at", ""), reverse=True)
    return entries
