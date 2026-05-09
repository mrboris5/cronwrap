"""User feedback / notes attached to specific job runs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_MAX_ENTRIES = 500


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_feedback(path: str) -> dict[str, list[dict[str, Any]]]:
    """Load feedback store; returns empty dict on missing / corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_feedback(path: str, data: dict[str, list[dict[str, Any]]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def add_feedback(
    path: str,
    job_id: str,
    run_id: str,
    rating: int,
    comment: str = "",
    author: str = "",
) -> dict[str, Any]:
    """Append a feedback entry for a job run.

    *rating* should be 1-5.  Values are clamped to that range.
    """
    rating = max(1, min(5, rating))
    entry: dict[str, Any] = {
        "run_id": run_id,
        "rating": rating,
        "comment": comment,
        "author": author,
        "timestamp": _now_iso(),
    }
    data = load_feedback(path)
    data.setdefault(job_id, []).append(entry)
    data[job_id] = data[job_id][-_MAX_ENTRIES:]
    save_feedback(path, data)
    return entry


def get_feedback(path: str, job_id: str) -> list[dict[str, Any]]:
    """Return all feedback entries for *job_id*."""
    return load_feedback(path).get(job_id, [])


def average_rating(path: str, job_id: str) -> float | None:
    """Return the average rating for *job_id*, or None if no entries."""
    entries = get_feedback(path, job_id)
    if not entries:
        return None
    return sum(e["rating"] for e in entries) / len(entries)


def remove_feedback(path: str, job_id: str, run_id: str) -> bool:
    """Remove feedback for a specific run.  Returns True if anything was removed."""
    data = load_feedback(path)
    before = len(data.get(job_id, []))
    data[job_id] = [e for e in data.get(job_id, []) if e["run_id"] != run_id]
    if len(data[job_id]) < before:
        save_feedback(path, data)
        return True
    return False
