"""Version tracking and comparison utilities for cronwrap jobs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_SENTINEL = object()


def load_versions(path: str) -> Dict[str, List[dict]]:
    """Load version records from a JSON file."""
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_versions(path: str, data: Dict[str, List[dict]]) -> None:
    """Persist version records to a JSON file."""
    Path(path).write_text(json.dumps(data, indent=2))


def set_version(path: str, job_id: str, version: str, metadata: Optional[dict] = None) -> dict:
    """Record a version string for a job.

    Args:
        path: Path to the versions JSON file.
        job_id: Identifier of the job.
        version: Version string (e.g. ``"1.2.3"`` or a git SHA).
        metadata: Optional extra key/value pairs to store alongside the version.

    Returns:
        The newly created version entry.
    """
    data = load_versions(path)
    entry: dict = {"version": version, "metadata": metadata or {}}
    data[job_id] = entry
    save_versions(path, data)
    return entry


def get_version(path: str, job_id: str) -> Optional[dict]:
    """Return the version entry for *job_id*, or ``None`` if not found."""
    return load_versions(path).get(job_id)


def remove_version(path: str, job_id: str) -> bool:
    """Remove the version entry for *job_id*.

    Returns:
        ``True`` if the entry existed and was removed, ``False`` otherwise.
    """
    data = load_versions(path)
    if job_id not in data:
        return False
    del data[job_id]
    save_versions(path, data)
    return True


def all_versions(path: str) -> Dict[str, dict]:
    """Return all version entries keyed by job ID."""
    return load_versions(path)
