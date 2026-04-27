"""Job execution policy: combine multiple preconditions into a named, reusable policy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_PATH = Path(".cronwrap_policies.json")


def load_policies(path: Path = _DEFAULT_PATH) -> dict[str, Any]:
    """Load policies from a JSON file. Returns empty dict on missing/corrupt file."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_policies(policies: dict[str, Any], path: Path = _DEFAULT_PATH) -> None:
    """Persist policies to a JSON file."""
    path.write_text(json.dumps(policies, indent=2))


def set_policy(name: str, rules: dict[str, Any], path: Path = _DEFAULT_PATH) -> dict[str, Any]:
    """Create or replace a named policy."""
    policies = load_policies(path)
    policies[name] = rules
    save_policies(policies, path)
    return policies[name]


def get_policy(name: str, path: Path = _DEFAULT_PATH) -> dict[str, Any] | None:
    """Return the policy dict for *name*, or None if not found."""
    return load_policies(path).get(name)


def remove_policy(name: str, path: Path = _DEFAULT_PATH) -> bool:
    """Remove a policy by name. Returns True if it existed."""
    policies = load_policies(path)
    if name not in policies:
        return False
    del policies[name]
    save_policies(policies, path)
    return True


def list_policies(path: Path = _DEFAULT_PATH) -> list[str]:
    """Return sorted list of policy names."""
    return sorted(load_policies(path).keys())


def apply_policy(name: str, job_cfg: dict[str, Any], path: Path = _DEFAULT_PATH) -> dict[str, Any]:
    """Merge a named policy into *job_cfg*, with job_cfg values taking precedence."""
    policy = get_policy(name, path)
    if policy is None:
        raise KeyError(f"Policy not found: {name!r}")
    merged = dict(policy)
    merged.update(job_cfg)
    return merged
