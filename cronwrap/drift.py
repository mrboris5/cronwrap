"""Detect and report schedule drift — the difference between expected
and actual run times for a cron job."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_MAX_ENTRIES = 200


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def load_drift(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_drift(path: str, data: dict) -> None:
    Path(path).write_text(json.dumps(data, indent=2))


def record_drift(
    path: str,
    job_id: str,
    expected_iso: str,
    actual_iso: Optional[str] = None,
) -> dict:
    """Record a drift entry comparing expected vs actual run time.

    If *actual_iso* is omitted the current UTC time is used.
    Returns the recorded entry.
    """
    actual_dt = _parse_iso(actual_iso) if actual_iso else _utcnow()
    expected_dt = _parse_iso(expected_iso)
    delta_seconds = (actual_dt - expected_dt).total_seconds()

    entry = {
        "job_id": job_id,
        "expected": expected_iso,
        "actual": actual_dt.isoformat(),
        "drift_seconds": round(delta_seconds, 3),
    }

    data = load_drift(path)
    records: List[dict] = data.get(job_id, [])
    records.append(entry)
    if len(records) > _MAX_ENTRIES:
        records = records[-_MAX_ENTRIES:]
    data[job_id] = records
    save_drift(path, data)
    return entry


def drift_stats(path: str, job_id: str) -> dict:
    """Return basic drift statistics for *job_id*."""
    data = load_drift(path)
    records = data.get(job_id, [])
    if not records:
        return {"job_id": job_id, "count": 0, "mean_seconds": None, "max_seconds": None}

    deltas = [r["drift_seconds"] for r in records]
    return {
        "job_id": job_id,
        "count": len(deltas),
        "mean_seconds": round(sum(deltas) / len(deltas), 3),
        "max_seconds": round(max(deltas, key=abs), 3),
    }


def last_drift(path: str, job_id: str) -> Optional[dict]:
    """Return the most recent drift entry for *job_id*, or None."""
    data = load_drift(path)
    records = data.get(job_id, [])
    return records[-1] if records else None
