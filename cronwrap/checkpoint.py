"""Checkpoint support: persist and restore job progress markers."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


def load_checkpoints(path: str) -> Dict[str, Any]:
    """Load checkpoint data from a JSON file."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_checkpoints(path: str, data: Dict[str, Any]) -> None:
    """Persist checkpoint data to a JSON file."""
    with open(path, "w") as f:
        json.dump(data, f)


def set_checkpoint(path: str, job_id: str, value: Any) -> None:
    """Set a checkpoint value for a job."""
    data = load_checkpoints(path)
    data[job_id] = value
    save_checkpoints(path, data)


def get_checkpoint(path: str, job_id: str, default: Any = None) -> Any:
    """Retrieve the checkpoint value for a job."""
    data = load_checkpoints(path)
    return data.get(job_id, default)


def clear_checkpoint(path: str, job_id: str) -> bool:
    """Remove the checkpoint for a job. Returns True if it existed."""
    data = load_checkpoints(path)
    if job_id not in data:
        return False
    del data[job_id]
    save_checkpoints(path, data)
    return True


def clear_all_checkpoints(path: str) -> int:
    """Remove all checkpoints. Returns the number removed."""
    data = load_checkpoints(path)
    count = len(data)
    save_checkpoints(path, {})
    return count
