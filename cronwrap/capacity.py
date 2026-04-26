"""Capacity tracking: record and check resource usage (CPU, memory) per job run."""

from __future__ import annotations

import json
import os
from typing import Any

_DEFAULT_MAX = 100


def _parse_percent(value: str) -> float:
    """Parse a percent string like '80%' or '80' into a float 0-100."""
    s = str(value).strip().rstrip("%")
    try:
        v = float(s)
    except ValueError:
        raise ValueError(f"Invalid percent value: {value!r}")
    if not (0.0 <= v <= 100.0):
        raise ValueError(f"Percent out of range [0, 100]: {v}")
    return v


def load_capacity(path: str) -> dict[str, list[dict[str, Any]]]:
    """Load capacity records from *path*; return empty dict on missing/corrupt file."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}


def save_capacity(path: str, data: dict[str, list[dict[str, Any]]]) -> None:
    """Persist capacity records to *path*."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def record_capacity(
    path: str,
    job_id: str,
    cpu_percent: float,
    mem_percent: float,
    timestamp: str,
    max_entries: int = _DEFAULT_MAX,
) -> dict[str, Any]:
    """Append a capacity sample for *job_id* and persist."""
    data = load_capacity(path)
    entry: dict[str, Any] = {
        "timestamp": timestamp,
        "cpu_percent": round(cpu_percent, 2),
        "mem_percent": round(mem_percent, 2),
    }
    records = data.setdefault(job_id, [])
    records.append(entry)
    if len(records) > max_entries:
        data[job_id] = records[-max_entries:]
    save_capacity(path, data)
    return entry


def is_over_capacity(
    path: str,
    job_id: str,
    cpu_limit: str | None = None,
    mem_limit: str | None = None,
) -> bool:
    """Return True if the most recent sample for *job_id* exceeds either limit."""
    data = load_capacity(path)
    records = data.get(job_id, [])
    if not records:
        return False
    latest = records[-1]
    if cpu_limit is not None:
        if latest["cpu_percent"] > _parse_percent(cpu_limit):
            return True
    if mem_limit is not None:
        if latest["mem_percent"] > _parse_percent(mem_limit):
            return True
    return False


def capacity_reason(
    path: str,
    job_id: str,
    cpu_limit: str | None = None,
    mem_limit: str | None = None,
) -> str:
    """Human-readable reason why a job is over capacity, or empty string."""
    data = load_capacity(path)
    records = data.get(job_id, [])
    if not records:
        return ""
    latest = records[-1]
    parts = []
    if cpu_limit is not None and latest["cpu_percent"] > _parse_percent(cpu_limit):
        parts.append(f"CPU {latest['cpu_percent']}% > limit {cpu_limit}")
    if mem_limit is not None and latest["mem_percent"] > _parse_percent(mem_limit):
        parts.append(f"MEM {latest['mem_percent']}% > limit {mem_limit}")
    return "; ".join(parts)
