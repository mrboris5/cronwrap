"""Retention policy storage: define per-job retention rules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_MAX = 200


def load_retention_policies(path: str) -> dict[str, Any]:
    """Load retention policies from a JSON file."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_retention_policies(path: str, policies: dict[str, Any]) -> None:
    """Persist retention policies to a JSON file."""
    Path(path).write_text(json.dumps(policies, indent=2))


def set_retention_policy(
    path: str,
    job_id: str,
    max_age_days: int | None = None,
    max_count: int | None = None,
) -> dict[str, Any]:
    """Set or update the retention policy for a job."""
    policies = load_retention_policies(path)
    entry: dict[str, Any] = policies.get(job_id, {})
    if max_age_days is not None:
        entry["max_age_days"] = max_age_days
    if max_count is not None:
        entry["max_count"] = max_count
    policies[job_id] = entry
    save_retention_policies(path, policies)
    return entry


def get_retention_policy(path: str, job_id: str) -> dict[str, Any]:
    """Return the retention policy for a job, or an empty dict."""
    return load_retention_policies(path).get(job_id, {})


def remove_retention_policy(path: str, job_id: str) -> bool:
    """Remove the retention policy for a job. Returns True if it existed."""
    policies = load_retention_policies(path)
    if job_id not in policies:
        return False
    del policies[job_id]
    save_retention_policies(path, policies)
    return True


def list_retention_policies(path: str) -> list[tuple[str, dict[str, Any]]]:
    """Return all (job_id, policy) pairs sorted by job_id."""
    policies = load_retention_policies(path)
    return sorted(policies.items())
