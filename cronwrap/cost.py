"""Track estimated compute cost per job run based on duration and a cost rate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

_DEFAULT_MAX = 500


def _parse_rate(rate: str) -> float:
    """Parse a cost rate string like '0.001/s', '0.06/m', '3.6/h'."""
    if "/" not in rate:
        raise ValueError(f"Invalid rate format: {rate!r}. Expected '<value>/<unit>'")
    value_str, unit = rate.split("/", 1)
    value = float(value_str)
    unit = unit.strip().lower()
    if unit == "s":
        return value
    if unit == "m":
        return value / 60.0
    if unit == "h":
        return value / 3600.0
    raise ValueError(f"Unknown rate unit: {unit!r}. Use s, m, or h.")


def load_costs(path: str) -> Dict[str, List[dict]]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, ValueError):
        return {}


def save_costs(path: str, data: Dict[str, List[dict]], max_entries: int = _DEFAULT_MAX) -> None:
    for job_id in data:
        data[job_id] = data[job_id][-max_entries:]
    Path(path).write_text(json.dumps(data, indent=2))


def record_cost(
    path: str,
    job_id: str,
    duration_seconds: float,
    rate: str,
    currency: str = "USD",
) -> dict:
    """Record a cost entry for a job run."""
    rate_per_sec = _parse_rate(rate)
    cost = round(duration_seconds * rate_per_sec, 6)
    data = load_costs(path)
    entry = {
        "duration_seconds": duration_seconds,
        "rate": rate,
        "cost": cost,
        "currency": currency,
    }
    data.setdefault(job_id, []).append(entry)
    save_costs(path, data)
    return entry


def total_cost(path: str, job_id: str) -> float:
    """Return total accumulated cost for a job."""
    data = load_costs(path)
    return round(sum(e["cost"] for e in data.get(job_id, [])), 6)


def cost_summary(path: str, job_id: str) -> dict:
    """Return a summary dict with count, total, average, and max cost."""
    data = load_costs(path)
    entries = data.get(job_id, [])
    if not entries:
        return {"count": 0, "total": 0.0, "average": 0.0, "max": 0.0}
    costs = [e["cost"] for e in entries]
    return {
        "count": len(costs),
        "total": round(sum(costs), 6),
        "average": round(sum(costs) / len(costs), 6),
        "max": round(max(costs), 6),
    }
