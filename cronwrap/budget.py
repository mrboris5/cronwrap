"""Runtime budget tracking: warn or block jobs that exceed a time budget."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_MAX = 100


def _parse_seconds(value: str) -> float:
    """Parse a duration string like '30s', '5m', '2h' into seconds."""
    value = value.strip()
    if value.endswith("s"):
        return float(value[:-1])
    if value.endswith("m"):
        return float(value[:-1]) * 60
    if value.endswith("h"):
        return float(value[:-1]) * 3600
    if value.endswith("d"):
        return float(value[:-1]) * 86400
    raise ValueError(f"Cannot parse duration: {value!r}")


def load_budgets(path: str) -> Dict[str, dict]:
    """Load budget state from a JSON file."""
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_budgets(path: str, data: Dict[str, dict]) -> None:
    """Persist budget state to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def record_duration(path: str, job_id: str, duration: float, max_entries: int = _DEFAULT_MAX) -> dict:
    """Append a duration sample for a job and return the updated entry."""
    data = load_budgets(path)
    entry = data.get(job_id, {"samples": [], "total": 0.0, "count": 0})
    entry["samples"].append(duration)
    entry["samples"] = entry["samples"][-max_entries:]
    entry["total"] = entry.get("total", 0.0) + duration
    entry["count"] = entry.get("count", 0) + 1
    data[job_id] = entry
    save_budgets(path, data)
    return entry


def is_over_budget(path: str, job_id: str, budget: str) -> bool:
    """Return True if the job's average duration exceeds the budget."""
    limit = _parse_seconds(budget)
    data = load_budgets(path)
    entry = data.get(job_id)
    if not entry or entry.get("count", 0) == 0:
        return False
    avg = entry["total"] / entry["count"]
    return avg > limit


def budget_reason(path: str, job_id: str, budget: str) -> Optional[str]:
    """Return a human-readable reason string if over budget, else None."""
    limit = _parse_seconds(budget)
    data = load_budgets(path)
    entry = data.get(job_id)
    if not entry or entry.get("count", 0) == 0:
        return None
    avg = entry["total"] / entry["count"]
    if avg > limit:
        return (
            f"job '{job_id}' average runtime {avg:.1f}s exceeds budget {limit:.1f}s"
        )
    return None


def clear_budget(path: str, job_id: str) -> bool:
    """Remove budget history for a job. Returns True if entry existed."""
    data = load_budgets(path)
    if job_id in data:
        del data[job_id]
        save_budgets(path, data)
        return True
    return False
