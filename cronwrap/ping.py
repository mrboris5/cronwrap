"""Ping tracking: record and query external ping/heartbeat URLs for jobs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_MAX = 200


def load_pings(path: str) -> Dict[str, List[dict]]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, ValueError):
        return {}


def save_pings(path: str, data: Dict[str, List[dict]], max_entries: int = DEFAULT_MAX) -> None:
    for job_id in data:
        data[job_id] = data[job_id][-max_entries:]
    Path(path).write_text(json.dumps(data, indent=2))


def set_ping_url(path: str, job_id: str, url: str, method: str = "GET") -> dict:
    data = load_pings(path)
    entry = {"url": url, "method": method.upper()}
    data[job_id] = [entry]
    save_pings(path, data)
    return entry


def get_ping_url(path: str, job_id: str) -> Optional[dict]:
    data = load_pings(path)
    entries = data.get(job_id, [])
    return entries[0] if entries else None


def remove_ping_url(path: str, job_id: str) -> bool:
    data = load_pings(path)
    if job_id not in data:
        return False
    del data[job_id]
    save_pings(path, data)
    return True


def send_ping(url: str, method: str = "GET", timeout: int = 10) -> bool:
    """Send an HTTP ping to the given URL. Returns True on success."""
    try:
        import urllib.request
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except Exception:
        return False


def ping_job(path: str, job_id: str, timeout: int = 10) -> Optional[bool]:
    """Look up the ping URL for job_id and send a ping. Returns None if not configured."""
    entry = get_ping_url(path, job_id)
    if entry is None:
        return None
    return send_ping(entry["url"], method=entry.get("method", "GET"), timeout=timeout)
