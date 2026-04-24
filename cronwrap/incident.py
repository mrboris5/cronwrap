"""Incident tracking: open, close, and query incidents for jobs."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

_DEFAULT_MAX = 200


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_incidents(path: str) -> list[dict[str, Any]]:
    """Load incidents from *path*; return empty list on missing/corrupt file."""
    if not os.path.exists(path):
        return []
    try:
        with open(path) as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_incidents(path: str, incidents: list[dict[str, Any]], max_entries: int = _DEFAULT_MAX) -> None:
    """Persist *incidents* to *path*, trimming to *max_entries*."""
    trimmed = incidents[-max_entries:]
    with open(path, "w") as fh:
        json.dump(trimmed, fh, indent=2)


def open_incident(path: str, job_id: str, reason: str, max_entries: int = _DEFAULT_MAX) -> dict[str, Any]:
    """Record a new open incident for *job_id*."""
    incidents = load_incidents(path)
    entry: dict[str, Any] = {
        "job_id": job_id,
        "status": "open",
        "reason": reason,
        "opened_at": _now_iso(),
        "closed_at": None,
    }
    incidents.append(entry)
    save_incidents(path, incidents, max_entries)
    return entry


def close_incident(path: str, job_id: str, resolution: str = "") -> dict[str, Any] | None:
    """Close the most recent open incident for *job_id*. Returns updated entry or None."""
    incidents = load_incidents(path)
    for entry in reversed(incidents):
        if entry.get("job_id") == job_id and entry.get("status") == "open":
            entry["status"] = "closed"
            entry["closed_at"] = _now_iso()
            entry["resolution"] = resolution
            save_incidents(path, incidents)
            return entry
    return None


def active_incidents(path: str, job_id: str | None = None) -> list[dict[str, Any]]:
    """Return all open incidents, optionally filtered by *job_id*."""
    incidents = load_incidents(path)
    return [
        e for e in incidents
        if e.get("status") == "open"
        and (job_id is None or e.get("job_id") == job_id)
    ]


def incident_history(path: str, job_id: str) -> list[dict[str, Any]]:
    """Return all incidents (open and closed) for *job_id*."""
    return [e for e in load_incidents(path) if e.get("job_id") == job_id]
