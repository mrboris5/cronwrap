"""Audit log: append-only record of job executions for compliance/review."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit_entry(
    job_id: str,
    command: str,
    exit_code: int,
    duration: float,
    tags: Optional[Dict[str, str]] = None,
    note: str = "",
) -> Dict[str, Any]:
    return {
        "ts": _now_iso(),
        "job_id": job_id,
        "command": command,
        "exit_code": exit_code,
        "duration": round(duration, 3),
        "tags": tags or {},
        "note": note,
    }


def append_audit(
    path: str,
    job_id: str,
    command: str,
    exit_code: int,
    duration: float,
    tags: Optional[Dict[str, str]] = None,
    note: str = "",
) -> Dict[str, Any]:
    """Append one audit entry (JSON line) to *path* and return the entry."""
    entry = _audit_entry(job_id, command, exit_code, duration, tags, note)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def read_audit(path: str, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read audit entries from *path*, optionally filtering by job_id."""
    if not os.path.exists(path):
        return []
    entries: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if job_id is None or entry.get("job_id") == job_id:
                entries.append(entry)
    return entries
