"""Execution trace recording for cron jobs."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

_MAX_ENTRIES = 200


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_traces(path: str) -> list[dict[str, Any]]:
    """Load trace records from *path*; return empty list on missing/corrupt file."""
    if not os.path.exists(path):
        return []
    try:
        with open(path) as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_traces(path: str, traces: list[dict[str, Any]], max_entries: int = _MAX_ENTRIES) -> None:
    """Persist *traces* to *path*, trimming to *max_entries*."""
    trimmed = traces[-max_entries:]
    with open(path, "w") as fh:
        json.dump(trimmed, fh, indent=2)


def record_trace(
    path: str,
    job_id: str,
    command: str,
    exit_code: int,
    duration: float,
    stdout: str = "",
    stderr: str = "",
    tags: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Append a trace entry for *job_id* and return the new entry."""
    traces = load_traces(path)
    entry: dict[str, Any] = {
        "job_id": job_id,
        "command": command,
        "exit_code": exit_code,
        "duration": round(duration, 4),
        "stdout": stdout,
        "stderr": stderr,
        "tags": tags or {},
        "recorded_at": _now_iso(),
    }
    traces.append(entry)
    save_traces(path, traces)
    return entry


def last_trace(path: str, job_id: str) -> dict[str, Any] | None:
    """Return the most recent trace entry for *job_id*, or None."""
    traces = load_traces(path)
    matches = [t for t in traces if t.get("job_id") == job_id]
    return matches[-1] if matches else None


def traces_for_job(path: str, job_id: str) -> list[dict[str, Any]]:
    """Return all trace entries for *job_id* in chronological order."""
    return [t for t in load_traces(path) if t.get("job_id") == job_id]
