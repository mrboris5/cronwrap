"""Job annotation support: attach free-form notes to job IDs."""

import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_FILE = ".cronwrap_annotations.json"


def load_annotations(path: str = _DEFAULT_FILE) -> Dict[str, List[str]]:
    """Load annotations from a JSON file. Returns empty dict on missing/corrupt file."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if isinstance(v, list)}
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_annotations(annotations: Dict[str, List[str]], path: str = _DEFAULT_FILE) -> None:
    """Persist annotations to a JSON file."""
    Path(path).write_text(json.dumps(annotations, indent=2))


def add_annotation(job_id: str, note: str, path: str = _DEFAULT_FILE) -> List[str]:
    """Append a note to the annotation list for *job_id*. Returns updated list."""
    if not note.strip():
        raise ValueError("Annotation note must not be empty.")
    annotations = load_annotations(path)
    annotations.setdefault(job_id, []).append(note.strip())
    save_annotations(annotations, path)
    return annotations[job_id]


def remove_annotation(job_id: str, index: int, path: str = _DEFAULT_FILE) -> List[str]:
    """Remove the note at *index* for *job_id*. Returns updated list."""
    annotations = load_annotations(path)
    notes = annotations.get(job_id, [])
    if index < 0 or index >= len(notes):
        raise IndexError(f"No annotation at index {index} for job '{job_id}'.")
    notes.pop(index)
    annotations[job_id] = notes
    save_annotations(annotations, path)
    return notes


def get_annotations(job_id: str, path: str = _DEFAULT_FILE) -> List[str]:
    """Return all notes for *job_id*, or an empty list."""
    return load_annotations(path).get(job_id, [])


def clear_annotations(job_id: str, path: str = _DEFAULT_FILE) -> None:
    """Delete all annotations for *job_id*."""
    annotations = load_annotations(path)
    annotations.pop(job_id, None)
    save_annotations(annotations, path)


def list_annotated_jobs(path: str = _DEFAULT_FILE) -> List[str]:
    """Return job IDs that have at least one annotation."""
    return [jid for jid, notes in load_annotations(path).items() if notes]
