"""Quota policy enforcement: cap how many times a job may run in a period."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

_DEFAULT_PATH = os.path.expanduser("~/.cronwrap/quota_policy.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_quota_policy(path: str = _DEFAULT_PATH) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_quota_policy(data: dict, path: str = _DEFAULT_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def set_quota(job_id: str, max_runs: int, period: str, path: str = _DEFAULT_PATH) -> dict:
    """Set a quota policy for a job.

    period: e.g. '1h', '24h', '7d'
    """
    data = load_quota_policy(path)
    data[job_id] = {
        "max_runs": max_runs,
        "period": period,
        "updated_at": _now_iso(),
    }
    save_quota_policy(data, path)
    return data[job_id]


def get_quota(job_id: str, path: str = _DEFAULT_PATH) -> Optional[dict]:
    data = load_quota_policy(path)
    return data.get(job_id)


def remove_quota(job_id: str, path: str = _DEFAULT_PATH) -> bool:
    data = load_quota_policy(path)
    if job_id not in data:
        return False
    del data[job_id]
    save_quota_policy(data, path)
    return True


def list_quotas(path: str = _DEFAULT_PATH) -> dict:
    return load_quota_policy(path)
