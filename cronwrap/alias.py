"""Job alias management — map short names to full job IDs."""

import json
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_PATH = Path(".cronwrap_aliases.json")


def load_aliases(path: Path = _DEFAULT_PATH) -> Dict[str, str]:
    """Load alias map from disk; returns empty dict if missing or corrupt."""
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_aliases(aliases: Dict[str, str], path: Path = _DEFAULT_PATH) -> None:
    """Persist alias map to disk."""
    path.write_text(json.dumps(aliases, indent=2))


def set_alias(alias: str, job_id: str, path: Path = _DEFAULT_PATH) -> Dict[str, str]:
    """Create or update an alias pointing to *job_id*."""
    aliases = load_aliases(path)
    aliases[alias] = job_id
    save_aliases(aliases, path)
    return aliases


def get_alias(alias: str, path: Path = _DEFAULT_PATH) -> Optional[str]:
    """Return the job_id for *alias*, or None if not found."""
    return load_aliases(path).get(alias)


def remove_alias(alias: str, path: Path = _DEFAULT_PATH) -> bool:
    """Remove *alias*; returns True if it existed, False otherwise."""
    aliases = load_aliases(path)
    if alias not in aliases:
        return False
    del aliases[alias]
    save_aliases(aliases, path)
    return True


def resolve(name: str, path: Path = _DEFAULT_PATH) -> str:
    """Return the job_id for *name*, falling back to *name* itself."""
    return get_alias(name, path) or name


def all_aliases(path: Path = _DEFAULT_PATH) -> Dict[str, str]:
    """Return the full alias map."""
    return load_aliases(path)
