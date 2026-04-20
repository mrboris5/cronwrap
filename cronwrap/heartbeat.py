"""Heartbeat tracking — record and check liveness of cron jobs."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

_MISSING = object()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_heartbeats(path: str) -> Dict[str, dict]:
    """Load heartbeat records from *path*; return {} on missing/corrupt file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_heartbeats(path: str, records: Dict[str, dict]) -> None:
    """Persist heartbeat *records* to *path* atomically."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(records, fh)
    os.replace(tmp, path)


def record_heartbeat(path: str, job_id: str, meta: Optional[dict] = None) -> dict:
    """Stamp *job_id* as alive right now and return the stored entry."""
    records = load_heartbeats(path)
    entry = {
        "job_id": job_id,
        "last_seen": _now_iso(),
        "meta": meta or {},
    }
    records[job_id] = entry
    save_heartbeats(path, records)
    return entry


def last_heartbeat(path: str, job_id: str) -> Optional[dict]:
    """Return the most recent heartbeat entry for *job_id*, or None."""
    return load_heartbeats(path).get(job_id)


def is_stale(path: str, job_id: str, max_age_seconds: float) -> bool:
    """Return True when *job_id* has not been seen within *max_age_seconds*."""
    entry = last_heartbeat(path, job_id)
    if entry is None:
        return True
    last = datetime.fromisoformat(entry["last_seen"])
    now = datetime.now(timezone.utc)
    # ensure both are offset-aware
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (now - last).total_seconds() > max_age_seconds


def stale_jobs(path: str, max_age_seconds: float) -> list:
    """Return a list of job_ids whose heartbeats are older than *max_age_seconds*."""
    records = load_heartbeats(path)
    result = []
    now = datetime.now(timezone.utc)
    for job_id, entry in records.items():
        last = datetime.fromisoformat(entry["last_seen"])
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if (now - last).total_seconds() > max_age_seconds:
            result.append(job_id)
    return result
