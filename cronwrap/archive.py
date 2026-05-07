"""Job run archive: compress and store old history entries."""
from __future__ import annotations

import gzip
import json
import os
from datetime import datetime, timezone
from typing import Any

DEFAULT_MAX_AGE_DAYS = 90


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def archive_entries(
    entries: list[dict[str, Any]],
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split entries into (keep, archive) based on age."""
    cutoff = (_utcnow().timestamp()) - max_age_days * 86400
    keep: list[dict[str, Any]] = []
    to_archive: list[dict[str, Any]] = []
    for entry in entries:
        ts_str = entry.get("timestamp", "")
        try:
            ts = _parse_iso(ts_str).timestamp()
        except (ValueError, TypeError):
            keep.append(entry)
            continue
        if ts < cutoff:
            to_archive.append(entry)
        else:
            keep.append(entry)
    return keep, to_archive


def write_archive(path: str, entries: list[dict[str, Any]]) -> int:
    """Append entries to a gzipped JSONL archive file. Returns count written."""
    if not entries:
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with gzip.open(path, "at", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")
    return len(entries)


def read_archive(path: str) -> list[dict[str, Any]]:
    """Read all entries from a gzipped JSONL archive file."""
    if not os.path.exists(path):
        return []
    results: list[dict[str, Any]] = []
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except (OSError, EOFError):
        return results
    return results


def archive_summary(path: str) -> dict[str, Any]:
    """Return summary stats for an archive file."""
    entries = read_archive(path)
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return {
        "entry_count": len(entries),
        "file_size_bytes": size,
        "path": path,
    }
