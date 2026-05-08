"""Mutual exclusion helpers for job execution slots."""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_MAX = 1


def load_mutex(path: str) -> Dict:
    """Load mutex state from a JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_mutex(path: str, state: Dict) -> None:
    """Persist mutex state to a JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def acquire_slot(path: str, job_id: str, pid: Optional[int] = None,
                 max_slots: int = _DEFAULT_MAX) -> bool:
    """Try to acquire a mutex slot for *job_id*.

    Returns True when the slot was acquired, False when the limit is reached.
    """
    state = load_mutex(path)
    entry = state.get(job_id, {"holders": [], "max": max_slots})
    holders: List[Dict] = entry.get("holders", [])
    # prune dead pids
    holders = [h for h in holders if _alive(h["pid"])]
    if len(holders) >= entry.get("max", max_slots):
        entry["holders"] = holders
        state[job_id] = entry
        save_mutex(path, state)
        return False
    holders.append({"pid": pid or os.getpid(), "acquired_at": time.time()})
    entry["holders"] = holders
    entry["max"] = max_slots
    state[job_id] = entry
    save_mutex(path, state)
    return True


def release_slot(path: str, job_id: str, pid: Optional[int] = None) -> bool:
    """Release the mutex slot held by *pid* for *job_id*.

    Returns True when a slot was removed, False otherwise.
    """
    state = load_mutex(path)
    if job_id not in state:
        return False
    target = pid or os.getpid()
    entry = state[job_id]
    before = len(entry["holders"])
    entry["holders"] = [h for h in entry["holders"] if h["pid"] != target]
    state[job_id] = entry
    save_mutex(path, state)
    return len(entry["holders"]) < before


def slot_count(path: str, job_id: str) -> int:
    """Return the number of active (live) holders for *job_id*."""
    state = load_mutex(path)
    entry = state.get(job_id, {})
    holders = [h for h in entry.get("holders", []) if _alive(h["pid"])]
    return len(holders)


def _alive(pid: int) -> bool:
    """Return True when *pid* is a running process."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
