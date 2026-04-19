"""Job dependency checking — ensure prerequisite jobs succeeded recently."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from cronwrap.history import load_history


def _now() -> datetime:
    return datetime.now(timezone.utc)


def last_success(job_id: str, history_file: str) -> Optional[datetime]:
    """Return the datetime of the most recent successful run, or None."""
    for entry in load_history(history_file):
        if entry.get("job_id") == job_id and entry.get("exit_code") == 0:
            ts = entry.get("timestamp")
            if ts:
                return datetime.fromisoformat(ts)
    return None


def dependency_met(
    dep_job_id: str,
    history_file: str,
    max_age_seconds: Optional[float] = None,
) -> bool:
    """Return True if dep_job_id succeeded (optionally within max_age_seconds)."""
    ts = last_success(dep_job_id, history_file)
    if ts is None:
        return False
    if max_age_seconds is not None:
        age = (_now() - ts).total_seconds()
        return age <= max_age_seconds
    return True


def check_dependencies(
    deps: List[str],
    history_file: str,
    max_age_seconds: Optional[float] = None,
) -> List[str]:
    """Return list of unmet dependency job IDs."""
    return [
        d for d in deps
        if not dependency_met(d, history_file, max_age_seconds)
    ]


def dependency_reason(unmet: List[str]) -> str:
    """Human-readable explanation of unmet dependencies."""
    if not unmet:
        return ""
    joined = ", ".join(unmet)
    return f"Unmet dependencies: {joined}"
