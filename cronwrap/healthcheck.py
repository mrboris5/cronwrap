"""Healthcheck endpoint state tracking for cronwrap jobs."""

import json
import os
from datetime import datetime, timezone
from typing import Optional

_MAX_ENTRIES = 200


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_healthchecks(path: str) -> dict:
    """Load healthcheck state from a JSON file."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_healthchecks(path: str, data: dict) -> None:
    """Persist healthcheck state to a JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def record_ping(path: str, job_id: str, status: str = "ok", detail: str = "") -> dict:
    """Record a healthcheck ping for a job.

    Args:
        path: Path to the healthcheck state file.
        job_id: Identifier for the job.
        status: One of 'ok', 'fail', or 'warn'.
        detail: Optional detail message.

    Returns:
        The recorded entry.
    """
    data = load_healthchecks(path)
    entry = {
        "job_id": job_id,
        "status": status,
        "detail": detail,
        "timestamp": _now_iso(),
    }
    history = data.get(job_id, [])
    history.append(entry)
    if len(history) > _MAX_ENTRIES:
        history = history[-_MAX_ENTRIES:]
    data[job_id] = history
    save_healthchecks(path, data)
    return entry


def last_ping(path: str, job_id: str) -> Optional[dict]:
    """Return the most recent healthcheck ping for a job, or None."""
    data = load_healthchecks(path)
    history = data.get(job_id, [])
    return history[-1] if history else None


def is_healthy(path: str, job_id: str) -> bool:
    """Return True if the most recent ping for a job has status 'ok'."""
    ping = last_ping(path, job_id)
    return ping is not None and ping.get("status") == "ok"


def all_job_ids(path: str) -> list:
    """Return all job IDs that have healthcheck records."""
    data = load_healthchecks(path)
    return list(data.keys())
