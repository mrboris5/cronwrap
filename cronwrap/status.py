"""Job status snapshot: current state derived from recent run history."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_PATH = Path("/var/lib/cronwrap/status.json")
_WINDOW = 10  # last N runs considered


def load_status(path: Path = _DEFAULT_PATH) -> Dict[str, dict]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_status(data: Dict[str, dict], path: Path = _DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def compute_status(job_id: str, runs: List[dict]) -> dict:
    """Derive a status dict from a list of run records (newest-first)."""
    recent = runs[:_WINDOW]
    if not recent:
        return {"job_id": job_id, "state": "unknown", "last_run": None, "consecutive_failures": 0}

    consecutive_failures = 0
    for r in recent:
        if r.get("exit_code", 1) != 0:
            consecutive_failures += 1
        else:
            break

    last = recent[0]
    if consecutive_failures == 0:
        state = "ok"
    elif consecutive_failures < 3:
        state = "degraded"
    else:
        state = "failing"

    return {
        "job_id": job_id,
        "state": state,
        "last_run": last.get("timestamp"),
        "last_exit_code": last.get("exit_code"),
        "consecutive_failures": consecutive_failures,
    }


def update_status(job_id: str, runs: List[dict], path: Path = _DEFAULT_PATH) -> dict:
    data = load_status(path)
    entry = compute_status(job_id, runs)
    data[job_id] = entry
    save_status(data, path)
    return entry


def get_status(job_id: str, path: Path = _DEFAULT_PATH) -> Optional[dict]:
    return load_status(path).get(job_id)


def all_statuses(path: Path = _DEFAULT_PATH) -> List[dict]:
    return list(load_status(path).values())
