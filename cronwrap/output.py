"""Output capture and storage for cron job runs."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

_DEFAULT_MAX = 50


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def load_outputs(path: str) -> Dict[str, List[dict]]:
    """Load stored outputs from *path*; return empty dict on missing/corrupt file."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}


def save_outputs(path: str, data: Dict[str, List[dict]]) -> None:
    """Persist *data* to *path* atomically."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)


def record_output(
    path: str,
    job_id: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    max_entries: int = _DEFAULT_MAX,
) -> dict:
    """Append a captured output entry for *job_id* and return the new entry."""
    data = load_outputs(path)
    entries = data.setdefault(job_id, [])
    entry = {
        "timestamp": _now_iso(),
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
    }
    entries.append(entry)
    if len(entries) > max_entries:
        entries[:] = entries[-max_entries:]
    save_outputs(path, data)
    return entry


def last_output(path: str, job_id: str) -> Optional[dict]:
    """Return the most recent output entry for *job_id*, or *None*."""
    data = load_outputs(path)
    entries = data.get(job_id, [])
    return entries[-1] if entries else None


def get_outputs(path: str, job_id: str, limit: int = 10) -> List[dict]:
    """Return up to *limit* most-recent output entries for *job_id*."""
    data = load_outputs(path)
    entries = data.get(job_id, [])
    return entries[-limit:]
