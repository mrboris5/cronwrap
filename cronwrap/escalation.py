"""Escalation policy: decide if an alert should be escalated based on consecutive failures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

_DEFAULT_THRESHOLD = 3


def load_state(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(path: str, state: Dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(state, indent=2))


def record_failure(path: str, job_id: str) -> int:
    """Increment consecutive failure count for job. Returns new count."""
    state = load_state(path)
    entry = state.get(job_id, {"consecutive_failures": 0})
    entry["consecutive_failures"] = entry.get("consecutive_failures", 0) + 1
    state[job_id] = entry
    save_state(path, state)
    return entry["consecutive_failures"]


def record_success(path: str, job_id: str) -> None:
    """Reset consecutive failure count on success."""
    state = load_state(path)
    if job_id in state:
        state[job_id]["consecutive_failures"] = 0
        save_state(path, state)


def should_escalate(path: str, job_id: str, threshold: int = _DEFAULT_THRESHOLD) -> bool:
    """Return True if consecutive failures meet or exceed threshold."""
    state = load_state(path)
    count = state.get(job_id, {}).get("consecutive_failures", 0)
    return count >= threshold


def escalation_reason(path: str, job_id: str, threshold: int = _DEFAULT_THRESHOLD) -> str:
    state = load_state(path)
    count = state.get(job_id, {}).get("consecutive_failures", 0)
    return (
        f"{job_id} has {count} consecutive failure(s) "
        f"(threshold={threshold})"
    )
