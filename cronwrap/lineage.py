"""Job lineage tracking — record parent/child relationships between job runs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_MAX = 500


def load_lineage(path: str) -> Dict[str, List[dict]]:
    """Load lineage records from *path*; return empty dict on missing/corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_lineage(path: str, data: Dict[str, List[dict]], max_entries: int = _DEFAULT_MAX) -> None:
    """Persist lineage data, trimming each job's list to *max_entries*."""
    trimmed = {job: entries[-max_entries:] for job, entries in data.items()}
    Path(path).write_text(json.dumps(trimmed, indent=2))


def record_lineage(
    path: str,
    job_id: str,
    run_id: str,
    parent_run_id: Optional[str] = None,
    triggered_by: Optional[str] = None,
    max_entries: int = _DEFAULT_MAX,
) -> dict:
    """Append a lineage entry for *job_id* and return the new entry."""
    data = load_lineage(path)
    entry: dict = {"run_id": run_id}
    if parent_run_id is not None:
        entry["parent_run_id"] = parent_run_id
    if triggered_by is not None:
        entry["triggered_by"] = triggered_by
    data.setdefault(job_id, []).append(entry)
    save_lineage(path, data, max_entries)
    return entry


def get_lineage(path: str, job_id: str) -> List[dict]:
    """Return all lineage entries for *job_id*, oldest first."""
    return load_lineage(path).get(job_id, [])


def find_children(path: str, parent_run_id: str) -> List[dict]:
    """Return all entries across all jobs whose parent_run_id matches."""
    results: List[dict] = []
    for job_id, entries in load_lineage(path).items():
        for entry in entries:
            if entry.get("parent_run_id") == parent_run_id:
                results.append({"job_id": job_id, **entry})
    return results


def lineage_summary(path: str, job_id: str) -> str:
    """Return a human-readable summary of lineage depth for *job_id*."""
    entries = get_lineage(path, job_id)
    total = len(entries)
    with_parent = sum(1 for e in entries if "parent_run_id" in e)
    return (
        f"job={job_id} total_runs={total} "
        f"child_runs={with_parent} root_runs={total - with_parent}"
    )
