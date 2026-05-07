"""Per-job free-text notes store."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_PATH = Path(".cronwrap") / "notes.json"
_MAX_NOTES = 50


def load_notes(path: Path = _DEFAULT_PATH) -> Dict[str, List[str]]:
    """Return the full notes mapping, or empty dict on error."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_notes(notes: Dict[str, List[str]], path: Path = _DEFAULT_PATH) -> None:
    """Persist notes to *path*, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notes, indent=2))


def add_note(job_id: str, text: str, path: Path = _DEFAULT_PATH) -> List[str]:
    """Append *text* to the note list for *job_id* and return updated list."""
    notes = load_notes(path)
    bucket = notes.setdefault(job_id, [])
    bucket.append(text)
    if len(bucket) > _MAX_NOTES:
        bucket = bucket[-_MAX_NOTES:]
        notes[job_id] = bucket
    save_notes(notes, path)
    return bucket


def remove_note(job_id: str, index: int, path: Path = _DEFAULT_PATH) -> Optional[str]:
    """Remove note at *index* for *job_id*. Returns removed text or None."""
    notes = load_notes(path)
    bucket = notes.get(job_id, [])
    if index < 0 or index >= len(bucket):
        return None
    removed = bucket.pop(index)
    notes[job_id] = bucket
    save_notes(notes, path)
    return removed


def get_notes(job_id: str, path: Path = _DEFAULT_PATH) -> List[str]:
    """Return all notes for *job_id*."""
    return load_notes(path).get(job_id, [])


def clear_notes(job_id: str, path: Path = _DEFAULT_PATH) -> int:
    """Delete all notes for *job_id*. Returns count removed."""
    notes = load_notes(path)
    count = len(notes.pop(job_id, []))
    save_notes(notes, path)
    return count
