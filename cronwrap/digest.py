"""Periodic digest report: aggregate run summaries over a time window."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

from cronwrap.history import load_history
from cronwrap.metrics import load_metrics


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_hours(window: str) -> int:
    """Parse a window string like '24h', '48h', or plain int hours."""
    window = window.strip()
    if window.endswith("h"):
        return int(window[:-1])
    if window.endswith("d"):
        return int(window[:-1]) * 24
    return int(window)


def runs_in_window(
    history_path: str, job_id: str, hours: int
) -> List[Dict[str, Any]]:
    """Return history entries for *job_id* within the last *hours* hours."""
    cutoff = _utcnow() - timedelta(hours=hours)
    entries = load_history(history_path, job_id)
    result = []
    for entry in entries:
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                result.append(entry)
        except (KeyError, ValueError):
            continue
    return result


def digest_for_job(
    history_path: str, metrics_path: str, job_id: str, window: str = "24h"
) -> Dict[str, Any]:
    """Build a digest dict for a single job over the given window."""
    hours = _parse_hours(window)
    entries = runs_in_window(history_path, job_id, hours)
    total = len(entries)
    successes = sum(1 for e in entries if e.get("exit_code", 1) == 0)
    failures = total - successes
    durations = [e["duration"] for e in entries if "duration" in e]
    avg_dur = sum(durations) / len(durations) if durations else 0.0
    return {
        "job_id": job_id,
        "window": window,
        "total_runs": total,
        "successes": successes,
        "failures": failures,
        "success_rate": round(successes / total, 4) if total else 0.0,
        "avg_duration": round(avg_dur, 3),
    }


def format_digest(digest: Dict[str, Any]) -> str:
    """Return a human-readable string for a digest entry."""
    sr = digest["success_rate"] * 100
    return (
        f"[{digest['job_id']}] window={digest['window']} "
        f"runs={digest['total_runs']} "
        f"ok={digest['successes']} fail={digest['failures']} "
        f"success_rate={sr:.1f}% avg_dur={digest['avg_duration']}s"
    )


def print_digest(digests: List[Dict[str, Any]]) -> None:
    """Print all digest entries to stdout."""
    for d in digests:
        print(format_digest(d))
