"""Job manifest: load and save a registry of known jobs with metadata."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_MAX = 500


def load_manifest(path: str) -> dict[str, dict[str, Any]]:
    """Load job manifest from *path*; return empty dict on missing/corrupt file."""
    try:
        data = json.loads(Path(path).read_text())
        if isinstance(data, dict):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def save_manifest(path: str, manifest: dict[str, dict[str, Any]]) -> None:
    """Persist *manifest* to *path* as JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, indent=2))


def register_job(
    path: str,
    job_id: str,
    command: str,
    schedule: str = "",
    tags: list[str] | None = None,
    description: str = "",
) -> dict[str, Any]:
    """Add or update a job entry in the manifest."""
    manifest = load_manifest(path)
    entry: dict[str, Any] = {
        "job_id": job_id,
        "command": command,
        "schedule": schedule,
        "tags": tags or [],
        "description": description,
    }
    manifest[job_id] = entry
    save_manifest(path, manifest)
    return entry


def get_job(path: str, job_id: str) -> dict[str, Any] | None:
    """Return the manifest entry for *job_id*, or None if not found."""
    return load_manifest(path).get(job_id)


def remove_job(path: str, job_id: str) -> bool:
    """Remove *job_id* from the manifest. Return True if it existed."""
    manifest = load_manifest(path)
    if job_id not in manifest:
        return False
    del manifest[job_id]
    save_manifest(path, manifest)
    return True


def list_jobs(path: str) -> list[dict[str, Any]]:
    """Return all manifest entries as a list, sorted by job_id."""
    manifest = load_manifest(path)
    return [manifest[k] for k in sorted(manifest)]
