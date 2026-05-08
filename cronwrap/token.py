"""Token bucket rate limiting for job execution."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any

_DEFAULT_MAX = 100


def _now() -> float:
    return time.time()


def load_tokens(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_tokens(path: str, data: Dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(data, indent=2))


def refill(entry: Dict[str, Any], rate: float, capacity: float) -> Dict[str, Any]:
    """Return an updated entry after refilling tokens based on elapsed time."""
    now = _now()
    elapsed = now - entry.get("last_refill", now)
    tokens = entry.get("tokens", capacity)
    tokens = min(capacity, tokens + elapsed * rate)
    return {"tokens": tokens, "last_refill": now}


def consume_token(path: str, job_id: str, rate: float = 1.0, capacity: float = 10.0) -> bool:
    """Try to consume one token for job_id. Returns True if allowed."""
    data = load_tokens(path)
    entry = data.get(job_id, {"tokens": capacity, "last_refill": _now()})
    entry = refill(entry, rate, capacity)
    if entry["tokens"] < 1.0:
        data[job_id] = entry
        save_tokens(path, data)
        return False
    entry["tokens"] -= 1.0
    data[job_id] = entry
    save_tokens(path, data)
    return True


def available_tokens(path: str, job_id: str, rate: float = 1.0, capacity: float = 10.0) -> float:
    """Return the current number of available tokens without consuming."""
    data = load_tokens(path)
    entry = data.get(job_id, {"tokens": capacity, "last_refill": _now()})
    entry = refill(entry, rate, capacity)
    return round(entry["tokens"], 4)


def reset_tokens(path: str, job_id: str, capacity: float = 10.0) -> None:
    """Reset tokens for a job to full capacity."""
    data = load_tokens(path)
    data[job_id] = {"tokens": capacity, "last_refill": _now()}
    save_tokens(path, data)
