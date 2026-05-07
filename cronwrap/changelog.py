"""Job changelog: record and retrieve configuration change events."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

MAX_ENTRIES = 500


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_changelog(path: str) -> List[Dict[str, Any]]:
    """Load changelog entries from *path*; return [] on missing/corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_changelog(path: str, entries: List[Dict[str, Any]]) -> None:
    """Persist *entries* to *path*, trimming to MAX_ENTRIES."""
    Path(path).write_text(json.dumps(entries[-MAX_ENTRIES:], indent=2))


def record_change(
    path: str,
    job_id: str,
    field: str,
    old_value: Any,
    new_value: Any,
    author: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a change event and return the new entry."""
    entries = load_changelog(path)
    entry: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "job_id": job_id,
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
    }
    if author is not None:
        entry["author"] = author
    entries.append(entry)
    save_changelog(path, entries)
    return entry


def get_changes(
    path: str, job_id: str, field: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return changelog entries for *job_id*, optionally filtered by *field*."""
    entries = load_changelog(path)
    results = [e for e in entries if e.get("job_id") == job_id]
    if field is not None:
        results = [e for e in results if e.get("field") == field]
    return results


def clear_changelog(path: str, job_id: str) -> int:
    """Remove all entries for *job_id*; return number of entries removed."""
    entries = load_changelog(path)
    kept = [e for e in entries if e.get("job_id") != job_id]
    removed = len(entries) - len(kept)
    save_changelog(path, kept)
    return removed
