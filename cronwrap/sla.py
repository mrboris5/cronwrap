"""SLA (Service Level Agreement) tracking for cron jobs."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_MAX_ENTRIES = 500


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_sla_records(path: str) -> dict:
    """Load SLA records from a JSON file."""
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_sla_records(path: str, records: dict, max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
    """Save SLA records to a JSON file, trimming per-job history."""
    for job_id in records:
        if isinstance(records[job_id].get("history"), list):
            records[job_id]["history"] = records[job_id]["history"][-max_entries:]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(records, indent=2))


def record_sla_run(path: str, job_id: str, duration: float, success: bool,
                   budget_seconds: Optional[float] = None) -> dict:
    """Record a completed run and evaluate SLA compliance."""
    records = load_sla_records(path)
    entry = records.setdefault(job_id, {"history": [], "violations": 0, "total": 0})

    breached = budget_seconds is not None and duration > budget_seconds
    run = {
        "timestamp": _now_iso(),
        "duration": round(duration, 3),
        "success": success,
        "breached": breached,
    }
    entry["history"].append(run)
    entry["total"] = entry.get("total", 0) + 1
    if breached or not success:
        entry["violations"] = entry.get("violations", 0) + 1
    entry["last_run"] = run["timestamp"]

    save_sla_records(path, records)
    return run


def sla_compliance(path: str, job_id: str) -> float:
    """Return compliance rate (0.0–1.0) for a job. 1.0 if no runs."""
    records = load_sla_records(path)
    entry = records.get(job_id, {})
    total = entry.get("total", 0)
    if total == 0:
        return 1.0
    violations = entry.get("violations", 0)
    return round(1.0 - violations / total, 4)


def sla_summary(path: str, job_id: str) -> dict:
    """Return a summary dict for a job's SLA status."""
    records = load_sla_records(path)
    entry = records.get(job_id, {"history": [], "violations": 0, "total": 0})
    return {
        "job_id": job_id,
        "total": entry.get("total", 0),
        "violations": entry.get("violations", 0),
        "compliance": sla_compliance(path, job_id),
        "last_run": entry.get("last_run"),
    }
