"""Formatted reports for tag-based job groupings."""

from __future__ import annotations

from typing import Dict, List

from cronwrap.grouping import group_by_tag, tag_summary
from cronwrap.metrics import JobMetrics


def format_tag_section(tag: str, job_ids: List[str]) -> str:
    """Return a formatted section string for a single tag."""
    lines = [f"[{tag}]"]
    for job_id in sorted(job_ids):
        lines.append(f"  - {job_id}")
    return "\n".join(lines)


def format_tag_report(
    metrics: Dict[str, JobMetrics],
    tag_key: str = "env",
) -> str:
    """Return a full tag-grouped report string.

    Args:
        metrics: Mapping of job_id -> JobMetrics.
        tag_key: The tag key to group by.

    Returns:
        Multi-line report string.
    """
    groups = group_by_tag(metrics, tag_key)
    summary = tag_summary(groups)

    lines: List[str] = []
    lines.append(f"Tag Report  (key={tag_key!r})")
    lines.append("=" * 40)

    if not groups:
        lines.append("  (no jobs)")
        return "\n".join(lines)

    for tag, job_ids in sorted(groups.items()):
        lines.append(format_tag_section(tag, job_ids))

    lines.append("")
    lines.append("Summary")
    lines.append("-" * 20)
    for tag, count in sorted(summary.items()):
        lines.append(f"  {tag}: {count} job(s)")

    return "\n".join(lines)


def print_tag_report(
    metrics: Dict[str, JobMetrics],
    tag_key: str = "env",
) -> None:
    """Print the tag report to stdout."""
    print(format_tag_report(metrics, tag_key))
