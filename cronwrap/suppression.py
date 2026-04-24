"""Suppression: temporarily silence alerts for a job."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_MAX = 256


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load_suppressions(path: str) -> Dict[str, dict]:
    """Load suppression state from *path*; return empty dict on missing/corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_suppressions(path: str, data: Dict[str, dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def suppress_job(
    path: str,
    job_id: str,
    duration_seconds: int,
    reason: str = "",
) -> dict:
    """Suppress alerts for *job_id* for *duration_seconds* seconds."""
    data = load_suppressions(path)
    until = datetime.fromtimestamp(
        _now().timestamp() + duration_seconds, tz=timezone.utc
    ).isoformat()
    entry = {
        "job_id": job_id,
        "suppressed_at": _now_iso(),
        "until": until,
        "reason": reason,
    }
    data[job_id] = entry
    save_suppressions(path, data)
    return entry


def unsuppress_job(path: str, job_id: str) -> bool:
    """Remove suppression for *job_id*. Returns True if it existed."""
    data = load_suppressions(path)
    if job_id in data:
        del data[job_id]
        save_suppressions(path, data)
        return True
    return False


def is_suppressed(path: str, job_id: str) -> bool:
    """Return True if *job_id* has an active (non-expired) suppression."""
    data = load_suppressions(path)
    entry = data.get(job_id)
    if not entry:
        return False
    try:
        until = datetime.fromisoformat(entry["until"])
    except (KeyError, ValueError):
        return False
    return _now() < until


def suppression_reason(path: str, job_id: str) -> Optional[str]:
    """Return a human-readable reason string if suppressed, else None."""
    if not is_suppressed(path, job_id):
        return None
    data = load_suppressions(path)
    entry = data[job_id]
    msg = f"alerts suppressed until {entry['until']}"
    if entry.get("reason"):
        msg += f" ({entry['reason']})"
    return msg


def list_suppressions(path: str) -> List[dict]:
    """Return all active suppression entries."""
    data = load_suppressions(path)
    now = _now()
    active = []
    for entry in data.values():
        try:
            until = datetime.fromisoformat(entry["until"])
        except (KeyError, ValueError):
            continue
        if now < until:
            active.append(entry)
    return active
