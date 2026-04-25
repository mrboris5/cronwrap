"""Replay support: record and re-execute failed job commands."""
from __future__ import annotations

import json
import os
from typing import Any

_DEFAULT_MAX = 100


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def load_replays(path: str) -> list[dict[str, Any]]:
    """Load replay entries from *path*; return empty list if missing/corrupt."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_replays(path: str, entries: list[dict[str, Any]], max_entries: int = _DEFAULT_MAX) -> None:
    """Persist *entries* to *path*, trimming to *max_entries*."""
    trimmed = entries[-max_entries:] if len(entries) > max_entries else entries
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(trimmed, fh, indent=2)


def record_replay(
    path: str,
    job_id: str,
    command: str,
    exit_code: int,
    stdout: str = "",
    stderr: str = "",
    max_entries: int = _DEFAULT_MAX,
) -> dict[str, Any]:
    """Append a replay entry for a failed run; return the new entry."""
    entries = load_replays(path)
    entry: dict[str, Any] = {
        "job_id": job_id,
        "command": command,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "recorded_at": _now_iso(),
        "replayed": False,
        "replay_at": None,
    }
    entries.append(entry)
    save_replays(path, entries, max_entries)
    return entry


def mark_replayed(path: str, job_id: str, command: str) -> bool:
    """Mark the most recent matching entry as replayed; return True if found."""
    entries = load_replays(path)
    for entry in reversed(entries):
        if entry.get("job_id") == job_id and entry.get("command") == command and not entry.get("replayed"):
            entry["replayed"] = True
            entry["replay_at"] = _now_iso()
            save_replays(path, entries)
            return True
    return False


def pending_replays(path: str, job_id: str | None = None) -> list[dict[str, Any]]:
    """Return entries not yet replayed, optionally filtered by *job_id*."""
    entries = load_replays(path)
    return [
        e for e in entries
        if not e.get("replayed") and (job_id is None or e.get("job_id") == job_id)
    ]
