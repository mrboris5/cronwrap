"""Formatted runbook report utilities."""

from __future__ import annotations

from typing import Dict, List, Optional

from cronwrap.runbook import load_runbooks

_LABELS: Dict[str, str] = {
    "url": "URL",
    "notes": "Notes",
    "owner": "Owner",
    "escalation_contact": "Escalation Contact",
}


def format_runbook_entry(job_id: str, entry: Dict[str, str]) -> str:
    """Return a human-readable block for a single runbook entry."""
    lines = [f"Job: {job_id}"]
    lines.append("-" * (len(job_id) + 5))
    for field, label in _LABELS.items():
        value = entry.get(field)
        if value:
            lines.append(f"  {label}: {value}")
    if len(lines) == 2:
        lines.append("  (no details recorded)")
    return "\n".join(lines)


def format_runbook_summary(path: str) -> str:
    """Return a full report of all runbook entries."""
    store = load_runbooks(path)
    if not store:
        return "No runbook entries found."
    blocks = [format_runbook_entry(job_id, entry) for job_id, entry in sorted(store.items())]
    header = f"Runbook Report ({len(store)} job(s))"
    separator = "=" * len(header)
    return "\n\n".join([f"{header}\n{separator}"] + blocks)


def print_runbook_report(path: str) -> None:
    """Print the full runbook report to stdout."""
    print(format_runbook_summary(path))
