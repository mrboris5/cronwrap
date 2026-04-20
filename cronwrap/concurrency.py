"""Concurrency limit enforcement for cron jobs.

Allows capping the number of simultaneously running instances
of a job by tracking active PIDs in a shared state file.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import List


def _alive(pid: int) -> bool:
    """Return True if a process with *pid* is currently running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def load_active(state_file: str) -> List[int]:
    """Load the list of active PIDs from *state_file*.

    Returns an empty list if the file is missing or corrupt.
    """
    path = Path(state_file)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [int(p) for p in data.get("pids", [])]
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def save_active(state_file: str, pids: List[int]) -> None:
    """Persist *pids* to *state_file*."""
    path = Path(state_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pids": pids}))


def prune_dead(pids: List[int]) -> List[int]:
    """Return only PIDs that correspond to running processes."""
    return [p for p in pids if _alive(p)]


def is_concurrency_limited(state_file: str, max_concurrent: int) -> bool:
    """Return True if the number of live instances meets or exceeds *max_concurrent*."""
    if max_concurrent <= 0:
        return False
    pids = prune_dead(load_active(state_file))
    return len(pids) >= max_concurrent


def register_pid(state_file: str, pid: int | None = None) -> None:
    """Add the current (or given) PID to the active set."""
    pid = pid or os.getpid()
    pids = prune_dead(load_active(state_file))
    if pid not in pids:
        pids.append(pid)
    save_active(state_file, pids)


def unregister_pid(state_file: str, pid: int | None = None) -> None:
    """Remove the current (or given) PID from the active set."""
    pid = pid or os.getpid()
    pids = prune_dead(load_active(state_file))
    pids = [p for p in pids if p != pid]
    save_active(state_file, pids)


def concurrency_reason(state_file: str, max_concurrent: int) -> str:
    """Human-readable explanation of why the job is concurrency-limited."""
    pids = prune_dead(load_active(state_file))
    return (
        f"concurrency limit reached: {len(pids)}/{max_concurrent} instances running "
        f"(pids: {pids})"
    )
