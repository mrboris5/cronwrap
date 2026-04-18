"""Job run history tracking — persists RunResult records to a JSON file."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any

DEFAULT_HISTORY_FILE = "/var/log/cronwrap_history.json"
MAX_ENTRIES = 100


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_history(path: str = DEFAULT_HISTORY_FILE) -> List[Dict[str, Any]]:
    """Return list of history entries; empty list if file missing or corrupt."""
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


def save_history(entries: List[Dict[str, Any]], path: str = DEFAULT_HISTORY_FILE) -> None:
    """Persist entries to *path*, keeping at most MAX_ENTRIES recent records."""
    trimmed = entries[-MAX_ENTRIES:]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(trimmed, fh, indent=2)


def record_run(
    command: str,
    returncode: int,
    duration: float,
    stdout: str = "",
    stderr: str = "",
    path: str = DEFAULT_HISTORY_FILE,
) -> Dict[str, Any]:
    """Append a run entry and return it."""
    entry: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "command": command,
        "returncode": returncode,
        "duration": round(duration, 4),
        "success": returncode == 0,
        "stdout": stdout[:2000],
        "stderr": stderr[:2000],
    }
    entries = load_history(path)
    entries.append(entry)
    save_history(entries, path)
    return entry


def last_runs(n: int = 10, path: str = DEFAULT_HISTORY_FILE) -> List[Dict[str, Any]]:
    """Return the *n* most recent run entries."""
    return load_history(path)[-n:]
