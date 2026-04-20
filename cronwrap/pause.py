"""Pause/resume support for cronwrap jobs.

Allows individual jobs to be paused so they are skipped during execution,
with an optional expiry time after which the pause is lifted automatically.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

_DEFAULT_FILE = "/tmp/cronwrap_paused.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load_paused(path: str = _DEFAULT_FILE) -> dict:
    """Load the paused-jobs store from *path*."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}


def save_paused(data: dict, path: str = _DEFAULT_FILE) -> None:
    """Persist *data* to *path*."""
    with open(path, "w") as fh:
        json.dump(data, fh)


def pause_job(
    job_id: str,
    expires: Optional[str] = None,
    path: str = _DEFAULT_FILE,
) -> dict:
    """Mark *job_id* as paused.

    Parameters
    ----------
    job_id:  Identifier of the job to pause.
    expires: Optional ISO-8601 datetime string at which the pause expires.
    path:    Path to the paused-jobs store.

    Returns the entry that was written.
    """
    data = load_paused(path)
    entry = {"paused_at": _now_iso(), "expires": expires}
    data[job_id] = entry
    save_paused(data, path)
    return entry


def resume_job(job_id: str, path: str = _DEFAULT_FILE) -> bool:
    """Remove the pause for *job_id*.  Returns True if the job was paused."""
    data = load_paused(path)
    if job_id not in data:
        return False
    del data[job_id]
    save_paused(data, path)
    return True


def is_paused(job_id: str, path: str = _DEFAULT_FILE) -> bool:
    """Return True if *job_id* is currently paused (and the pause has not expired)."""
    data = load_paused(path)
    entry = data.get(job_id)
    if entry is None:
        return False
    expires = entry.get("expires")
    if expires is None:
        return True
    try:
        exp_dt = datetime.fromisoformat(expires)
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        return _now() < exp_dt
    except ValueError:
        return True


def pause_reason(job_id: str, path: str = _DEFAULT_FILE) -> str:
    """Human-readable explanation of why *job_id* is paused (or empty string)."""
    if not is_paused(job_id, path):
        return ""
    data = load_paused(path)
    entry = data.get(job_id, {})
    paused_at = entry.get("paused_at", "unknown")
    expires = entry.get("expires")
    if expires:
        return f"job '{job_id}' is paused since {paused_at} (expires {expires})"
    return f"job '{job_id}' is paused since {paused_at} (indefinitely)"
