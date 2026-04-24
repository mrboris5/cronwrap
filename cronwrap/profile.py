"""Job profiling: track and summarize per-job timing statistics."""

import json
import os
from typing import Dict, List, Optional


def load_profiles(path: str) -> Dict[str, List[float]]:
    """Load profiling data from *path*; return empty dict if missing/corrupt."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return {k: list(v) for k, v in data.items() if isinstance(v, list)}
    except (json.JSONDecodeError, ValueError):
        pass
    return {}


def save_profiles(path: str, profiles: Dict[str, List[float]]) -> None:
    """Persist *profiles* to *path* as JSON."""
    with open(path, "w") as fh:
        json.dump(profiles, fh)


def record_duration(
    path: str, job_id: str, duration: float, max_samples: int = 100
) -> None:
    """Append *duration* (seconds) for *job_id*, keeping at most *max_samples*."""
    profiles = load_profiles(path)
    samples = profiles.get(job_id, [])
    samples.append(round(duration, 4))
    if len(samples) > max_samples:
        samples = samples[-max_samples:]
    profiles[job_id] = samples
    save_profiles(path, profiles)


def profile_stats(path: str, job_id: str) -> Optional[Dict[str, float]]:
    """Return min/max/avg/p95 for *job_id*, or None if no data."""
    profiles = load_profiles(path)
    samples = profiles.get(job_id, [])
    if not samples:
        return None
    sorted_samples = sorted(samples)
    n = len(sorted_samples)
    avg = sum(sorted_samples) / n
    p95_idx = max(0, int(n * 0.95) - 1)
    return {
        "count": n,
        "min": sorted_samples[0],
        "max": sorted_samples[-1],
        "avg": round(avg, 4),
        "p95": sorted_samples[p95_idx],
    }


def clear_profile(path: str, job_id: str) -> bool:
    """Remove profiling data for *job_id*. Returns True if entry existed."""
    profiles = load_profiles(path)
    if job_id not in profiles:
        return False
    del profiles[job_id]
    save_profiles(path, profiles)
    return True
