"""Job output snapshot storage — save and retrieve recent command outputs."""

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

DEFAULT_MAX = 10


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_snapshots(path: str) -> List[dict]:
    """Load snapshots from a JSON file. Returns empty list on missing/corrupt file."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def save_snapshots(path: str, snapshots: List[dict], max_entries: int = DEFAULT_MAX) -> None:
    """Persist snapshots list, trimming to max_entries."""
    trimmed = snapshots[-max_entries:] if len(snapshots) > max_entries else snapshots
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(trimmed, f, indent=2)


def record_snapshot(
    path: str,
    job_id: str,
    command: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    max_entries: int = DEFAULT_MAX,
) -> dict:
    """Append a snapshot entry and persist. Returns the new entry."""
    snapshots = load_snapshots(path)
    entry = {
        "job_id": job_id,
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "timestamp": _now_iso(),
    }
    snapshots.append(entry)
    save_snapshots(path, snapshots, max_entries)
    return entry


def last_snapshot(path: str, job_id: str) -> Optional[dict]:
    """Return the most recent snapshot for a given job_id, or None."""
    snapshots = load_snapshots(path)
    for entry in reversed(snapshots):
        if entry.get("job_id") == job_id:
            return entry
    return None
