"""Slot-based execution limiter: cap how many times a job can run per time window."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List

_DEFAULTS: Dict = {}


def _utcnow() -> float:
    return time.time()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_seconds(value: str) -> int:
    """Parse a duration string like '30s', '5m', '2h', '1d' into seconds."""
    value = value.strip()
    if value.endswith("d"):
        return int(value[:-1]) * 86400
    if value.endswith("h"):
        return int(value[:-1]) * 3600
    if value.endswith("m"):
        return int(value[:-1]) * 60
    if value.endswith("s"):
        return int(value[:-1])
    raise ValueError(f"Invalid duration: {value!r}")


def load_slots(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_slots(path: str, data: Dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f)


def record_slot_use(path: str, job_id: str) -> Dict:
    data = load_slots(path)
    entry = data.get(job_id, {"uses": []})
    entry["uses"].append(_now_iso())
    data[job_id] = entry
    save_slots(path, data)
    return entry


def uses_in_window(path: str, job_id: str, window: str) -> List[str]:
    """Return list of ISO timestamps within the window."""
    seconds = _parse_seconds(window)
    cutoff = _utcnow() - seconds
    data = load_slots(path)
    uses = data.get(job_id, {}).get("uses", [])
    return [
        ts for ts in uses
        if datetime.fromisoformat(ts).timestamp() >= cutoff
    ]


def is_slot_exceeded(path: str, job_id: str, max_uses: int, window: str) -> bool:
    return len(uses_in_window(path, job_id, window)) >= max_uses


def slot_exceeded_reason(path: str, job_id: str, max_uses: int, window: str) -> str:
    count = len(uses_in_window(path, job_id, window))
    return (
        f"Job '{job_id}' has used {count}/{max_uses} slots in the last {window}."
    )


def reset_slots(path: str, job_id: str) -> None:
    data = load_slots(path)
    if job_id in data:
        data[job_id]["uses"] = []
        save_slots(path, data)
