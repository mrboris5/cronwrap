"""Job correlation: track related runs by correlation ID."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_PATH = Path(".cronwrap_correlations.json")
MAX_ENTRIES = 500


def _load(path: Path) -> Dict[str, List[dict]]:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data: Dict[str, List[dict]], path: Path) -> None:
    path.write_text(json.dumps(data, indent=2))


def new_correlation_id() -> str:
    """Generate a fresh correlation ID."""
    return str(uuid.uuid4())


def record_correlation(
    correlation_id: str,
    job_id: str,
    status: str,
    timestamp: str,
    *,
    path: Path = DEFAULT_PATH,
    extra: Optional[dict] = None,
) -> dict:
    """Attach a job run to a correlation ID."""
    data = _load(path)
    entry: dict = {
        "job_id": job_id,
        "status": status,
        "timestamp": timestamp,
    }
    if extra:
        entry.update(extra)
    runs = data.setdefault(correlation_id, [])
    runs.append(entry)
    # Trim oldest correlation IDs if over limit
    if len(data) > MAX_ENTRIES:
        oldest = sorted(data.keys())[: len(data) - MAX_ENTRIES]
        for key in oldest:
            del data[key]
    _save(data, path)
    return entry


def get_correlated_runs(
    correlation_id: str, *, path: Path = DEFAULT_PATH
) -> List[dict]:
    """Return all runs recorded under a correlation ID."""
    return _load(path).get(correlation_id, [])


def all_correlation_ids(*, path: Path = DEFAULT_PATH) -> List[str]:
    """Return all known correlation IDs."""
    return list(_load(path).keys())


def remove_correlation(correlation_id: str, *, path: Path = DEFAULT_PATH) -> bool:
    """Delete a correlation ID and all its runs. Returns True if it existed."""
    data = _load(path)
    if correlation_id not in data:
        return False
    del data[correlation_id]
    _save(data, path)
    return True
