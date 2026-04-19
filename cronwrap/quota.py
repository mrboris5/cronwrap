"""Quota management: daily/weekly run quotas per job."""

from __future__ import annotations

import json
import os
from typing import Dict


DEFAULT_MAX_ENTRIES = 500


def load_quotas(quota_file: str) -> Dict[str, int]:
    """Load quota usage counts from file. Returns {job_id: count}."""
    if not os.path.exists(quota_file):
        return {}
    try:
        with open(quota_file) as f:
            data = json.load(f)
        return {k: int(v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_quotas(quota_file: str, quotas: Dict[str, int]) -> None:
    """Persist quota usage counts to file."""
    with open(quota_file, "w") as f:
        json.dump(quotas, f)


def increment_quota(quota_file: str, job_id: str) -> int:
    """Increment and persist the run count for job_id. Returns new count."""
    quotas = load_quotas(quota_file)
    quotas[job_id] = quotas.get(job_id, 0) + 1
    save_quotas(quota_file, quotas)
    return quotas[job_id]


def reset_quota(quota_file: str, job_id: str) -> None:
    """Reset the run count for a specific job."""
    quotas = load_quotas(quota_file)
    quotas[job_id] = 0
    save_quotas(quota_file, quotas)


def reset_all_quotas(quota_file: str) -> None:
    """Reset all job quotas (e.g. at start of new day/week)."""
    save_quotas(quota_file, {})


def quota_exceeded(quota_file: str, job_id: str, limit: int) -> bool:
    """Return True if job_id has reached or exceeded limit runs."""
    quotas = load_quotas(quota_file)
    return quotas.get(job_id, 0) >= limit


def quota_status(quota_file: str, job_id: str, limit: int) -> str:
    """Return a human-readable quota status string."""
    quotas = load_quotas(quota_file)
    used = quotas.get(job_id, 0)
    return f"Job '{job_id}': {used}/{limit} runs used"


def get_quota_count(quota_file: str, job_id: str) -> int:
    """Return the current run count for job_id without modifying it.

    Args:
        quota_file: Path to the quota storage file.
        job_id: The job identifier to look up.

    Returns:
        The number of runs recorded for the job, or 0 if not found.
    """
    quotas = load_quotas(quota_file)
    return quotas.get(job_id, 0)
