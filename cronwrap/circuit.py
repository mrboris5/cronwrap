"""Circuit breaker for cron jobs — stops execution after too many consecutive failures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

DEFAULT_THRESHOLD = 3
DEFAULT_STATE: Dict[str, Any] = {"failures": 0, "open": False}


def load_state(path: str) -> Dict[str, Any]:
    """Load circuit breaker state from a JSON file."""
    p = Path(path)
    if not p.exists():
        return dict(DEFAULT_STATE)
    try:
        data = json.loads(p.read_text())
        return {
            "failures": int(data.get("failures", 0)),
            "open": bool(data.get("open", False)),
        }
    except (json.JSONDecodeError, ValueError):
        return dict(DEFAULT_STATE)


def save_state(path: str, state: Dict[str, Any]) -> None:
    """Persist circuit breaker state to a JSON file."""
    Path(path).write_text(json.dumps(state))


def is_open(path: str, threshold: int = DEFAULT_THRESHOLD) -> bool:
    """Return True if the circuit is open (job should be skipped)."""
    state = load_state(path)
    return state["open"] or state["failures"] >= threshold


def record_success(path: str) -> Dict[str, Any]:
    """Record a successful run — resets failure count and closes the circuit."""
    state = {"failures": 0, "open": False}
    save_state(path, state)
    return state


def record_failure(path: str, threshold: int = DEFAULT_THRESHOLD) -> Dict[str, Any]:
    """Record a failed run — increments counter and opens circuit if threshold reached."""
    state = load_state(path)
    state["failures"] += 1
    state["open"] = state["failures"] >= threshold
    save_state(path, state)
    return state


def open_reason(path: str, threshold: int = DEFAULT_THRESHOLD) -> str:
    """Return a human-readable reason why the circuit is open."""
    state = load_state(path)
    return (
        f"Circuit open after {state['failures']} consecutive failure(s) "
        f"(threshold={threshold})"
    )
