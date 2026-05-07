"""Formatting helpers for alert rule reports."""
from __future__ import annotations

from typing import Any, Dict, List

from cronwrap.alert_rule import list_rules


def format_rule_entry(entry: Dict[str, Any]) -> str:
    """Format a single alert rule entry for display."""
    job_id = entry.get("job_id", "unknown")
    condition = entry.get("condition", "?")
    threshold = entry.get("threshold", 0)
    channel = entry.get("channel", "email")
    enabled = entry.get("enabled", True)
    status = "enabled" if enabled else "disabled"
    return f"{job_id:30s}  {condition:5s}  {threshold:>10.2f}  {channel:10s}  [{status}]"


def format_rule_summary(entries: List[Dict[str, Any]]) -> str:
    """Format a table of alert rules."""
    if not entries:
        return "No alert rules defined."
    header = f"{'JOB':30s}  {'COND':5s}  {'THRESHOLD':>10s}  {'CHANNEL':10s}  STATUS"
    divider = "-" * len(header)
    lines = [header, divider]
    for e in entries:
        lines.append(format_rule_entry(e))
    total = len(entries)
    active = sum(1 for e in entries if e.get("enabled", True))
    lines.append(divider)
    lines.append(f"Total: {total}  Active: {active}  Disabled: {total - active}")
    return "\n".join(lines)


def print_alert_rule_report(path: str) -> None:
    """Print a formatted alert rule report to stdout."""
    entries = list_rules(path)
    print(format_rule_summary(entries))
