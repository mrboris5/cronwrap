"""Job labeling: attach, remove, and filter labels on job IDs."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Set

_DEFAULT_FILE = ".cronwrap_labels.json"


def load_labels(path: str = _DEFAULT_FILE) -> Dict[str, List[str]]:
    """Load label mapping {job_id: [label, ...]} from JSON file."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, ValueError):
        return {}


def save_labels(data: Dict[str, List[str]], path: str = _DEFAULT_FILE) -> None:
    """Persist label mapping to JSON file."""
    Path(path).write_text(json.dumps(data, indent=2))


def add_label(job_id: str, label: str, path: str = _DEFAULT_FILE) -> List[str]:
    """Add a label to a job; returns updated label list."""
    data = load_labels(path)
    labels: List[str] = data.get(job_id, [])
    if label not in labels:
        labels.append(label)
    data[job_id] = labels
    save_labels(data, path)
    return labels


def remove_label(job_id: str, label: str, path: str = _DEFAULT_FILE) -> List[str]:
    """Remove a label from a job; returns updated label list."""
    data = load_labels(path)
    labels = [l for l in data.get(job_id, []) if l != label]
    data[job_id] = labels
    save_labels(data, path)
    return labels


def get_labels(job_id: str, path: str = _DEFAULT_FILE) -> List[str]:
    """Return labels for a specific job."""
    return load_labels(path).get(job_id, [])


def jobs_with_label(label: str, path: str = _DEFAULT_FILE) -> List[str]:
    """Return all job IDs that carry the given label."""
    return [jid for jid, labels in load_labels(path).items() if label in labels]


def clear_labels(job_id: str, path: str = _DEFAULT_FILE) -> None:
    """Remove all labels for a job."""
    data = load_labels(path)
    data.pop(job_id, None)
    save_labels(data, path)
