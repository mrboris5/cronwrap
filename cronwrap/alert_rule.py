"""Alert rule storage and evaluation for cronwrap."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_DEFAULT_MAX = 500


def load_alert_rules(path: str) -> Dict[str, Any]:
    """Load alert rules from a JSON file."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_alert_rules(path: str, rules: Dict[str, Any]) -> None:
    """Persist alert rules to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rules, indent=2))


def set_alert_rule(
    path: str,
    job_id: str,
    condition: str,
    threshold: float,
    channel: str = "email",
    enabled: bool = True,
) -> Dict[str, Any]:
    """Create or update an alert rule for a job."""
    rules = load_alert_rules(path)
    entry = {
        "condition": condition,
        "threshold": threshold,
        "channel": channel,
        "enabled": enabled,
    }
    rules[job_id] = entry
    save_alert_rules(path, rules)
    return entry


def get_alert_rule(path: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Return the alert rule for a job, or None."""
    return load_alert_rules(path).get(job_id)


def remove_alert_rule(path: str, job_id: str) -> bool:
    """Remove the alert rule for a job. Returns True if it existed."""
    rules = load_alert_rules(path)
    if job_id not in rules:
        return False
    del rules[job_id]
    save_alert_rules(path, rules)
    return True


def evaluate_rule(rule: Dict[str, Any], value: float) -> bool:
    """Evaluate a rule condition against a numeric value."""
    if not rule.get("enabled", True):
        return False
    condition = rule.get("condition", "gt")
    threshold = float(rule.get("threshold", 0))
    if condition == "gt":
        return value > threshold
    if condition == "lt":
        return value < threshold
    if condition == "gte":
        return value >= threshold
    if condition == "lte":
        return value <= threshold
    if condition == "eq":
        return value == threshold
    return False


def list_rules(path: str) -> List[Dict[str, Any]]:
    """Return all alert rules as a list of dicts with job_id included."""
    rules = load_alert_rules(path)
    return [{"job_id": k, **v} for k, v in rules.items()]
