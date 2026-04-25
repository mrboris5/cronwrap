"""Job ownership tracking — assign owners/teams to jobs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_PATH = Path(".cronwrap_ownership.json")


def load_owners(path: Path = _DEFAULT_PATH) -> Dict[str, dict]:
    """Load ownership data from *path*; return empty dict on missing/corrupt file."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_owners(data: Dict[str, dict], path: Path = _DEFAULT_PATH) -> None:
    """Persist ownership data to *path*."""
    path.write_text(json.dumps(data, indent=2))


def set_owner(
    job_id: str,
    owner: str,
    team: Optional[str] = None,
    email: Optional[str] = None,
    path: Path = _DEFAULT_PATH,
) -> dict:
    """Assign *owner* (and optional *team* / *email*) to *job_id*."""
    data = load_owners(path)
    entry: dict = {"owner": owner}
    if team is not None:
        entry["team"] = team
    if email is not None:
        entry["email"] = email
    data[job_id] = entry
    save_owners(data, path)
    return entry


def get_owner(job_id: str, path: Path = _DEFAULT_PATH) -> Optional[dict]:
    """Return ownership record for *job_id*, or ``None`` if not set."""
    return load_owners(path).get(job_id)


def remove_owner(job_id: str, path: Path = _DEFAULT_PATH) -> bool:
    """Remove ownership record for *job_id*. Returns ``True`` if it existed."""
    data = load_owners(path)
    if job_id not in data:
        return False
    del data[job_id]
    save_owners(data, path)
    return True


def jobs_by_team(team: str, path: Path = _DEFAULT_PATH) -> List[str]:
    """Return list of job IDs whose team matches *team* (case-insensitive)."""
    team_lower = team.lower()
    return [
        jid
        for jid, entry in load_owners(path).items()
        if entry.get("team", "").lower() == team_lower
    ]


def all_owners(path: Path = _DEFAULT_PATH) -> Dict[str, dict]:
    """Return the full ownership mapping."""
    return load_owners(path)
