"""Baseline duration tracking: record expected durations and detect anomalies."""

import json
import os
from typing import Optional

DEFAULT_PATH = "/tmp/cronwrap_baselines.json"
_MARGIN_DEFAULT = 0.25  # 25% over baseline triggers a warning


def load_baselines(path: str = DEFAULT_PATH) -> dict:
    """Load baselines from JSON file; return empty dict on missing/corrupt."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}


def save_baselines(data: dict, path: str = DEFAULT_PATH) -> None:
    """Persist baselines dict to JSON file."""
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def set_baseline(job_id: str, expected_seconds: float, path: str = DEFAULT_PATH) -> dict:
    """Set or update the expected duration baseline for a job."""
    if expected_seconds <= 0:
        raise ValueError("expected_seconds must be positive")
    data = load_baselines(path)
    data[job_id] = {"expected_seconds": expected_seconds}
    save_baselines(data, path)
    return data[job_id]


def get_baseline(job_id: str, path: str = DEFAULT_PATH) -> Optional[float]:
    """Return expected_seconds for job_id, or None if not set."""
    data = load_baselines(path)
    entry = data.get(job_id)
    if entry is None:
        return None
    return entry.get("expected_seconds")


def remove_baseline(job_id: str, path: str = DEFAULT_PATH) -> bool:
    """Remove baseline for job_id. Returns True if removed, False if not found."""
    data = load_baselines(path)
    if job_id not in data:
        return False
    del data[job_id]
    save_baselines(data, path)
    return True


def check_baseline(
    job_id: str,
    actual_seconds: float,
    margin: float = _MARGIN_DEFAULT,
    path: str = DEFAULT_PATH,
) -> Optional[str]:
    """Return a warning string if actual_seconds exceeds baseline by margin, else None."""
    expected = get_baseline(job_id, path)
    if expected is None:
        return None
    threshold = expected * (1 + margin)
    if actual_seconds > threshold:
        pct = ((actual_seconds - expected) / expected) * 100
        return (
            f"Job '{job_id}' took {actual_seconds:.1f}s, "
            f"{pct:.0f}% over baseline of {expected:.1f}s"
        )
    return None
