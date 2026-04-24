"""Runbook support: attach notes/documentation URLs to job IDs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

RunbookStore = Dict[str, Dict[str, str]]

_FIELDS = ("url", "notes", "owner", "escalation_contact")


def load_runbooks(path: str) -> RunbookStore:
    """Load runbook entries from *path*; return empty dict on missing/corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_runbooks(path: str, store: RunbookStore) -> None:
    """Persist *store* to *path* as JSON."""
    Path(path).write_text(json.dumps(store, indent=2))


def set_runbook(
    path: str,
    job_id: str,
    *,
    url: Optional[str] = None,
    notes: Optional[str] = None,
    owner: Optional[str] = None,
    escalation_contact: Optional[str] = None,
) -> Dict[str, str]:
    """Create or update the runbook entry for *job_id*."""
    store = load_runbooks(path)
    entry = store.get(job_id, {})
    for field, value in [
        ("url", url),
        ("notes", notes),
        ("owner", owner),
        ("escalation_contact", escalation_contact),
    ]:
        if value is not None:
            entry[field] = value
    store[job_id] = entry
    save_runbooks(path, store)
    return entry


def get_runbook(path: str, job_id: str) -> Optional[Dict[str, str]]:
    """Return the runbook entry for *job_id*, or None if absent."""
    return load_runbooks(path).get(job_id)


def remove_runbook(path: str, job_id: str) -> bool:
    """Remove the runbook entry for *job_id*. Returns True if it existed."""
    store = load_runbooks(path)
    if job_id not in store:
        return False
    del store[job_id]
    save_runbooks(path, store)
    return True


def list_runbooks(path: str) -> List[str]:
    """Return all job IDs that have runbook entries."""
    return list(load_runbooks(path).keys())
