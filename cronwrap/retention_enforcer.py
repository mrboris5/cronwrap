"""Apply retention policies to job history records."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cronwrap.retention_policy import get_retention_policy


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp string into a timezone-aware datetime."""
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def apply_retention_policy(
    policy_path: str,
    job_id: str,
    records: list[dict[str, Any]],
    timestamp_key: str = "timestamp",
) -> list[dict[str, Any]]:
    """Filter *records* according to the job's retention policy.

    Records are expected to be sorted newest-first. The function applies
    ``max_count`` first, then ``max_age_days``.

    Returns the surviving records (newest-first).
    """
    policy = get_retention_policy(policy_path, job_id)
    if not policy:
        return records

    result = list(records)

    max_count: int | None = policy.get("max_count")
    if max_count is not None and max_count >= 0:
        result = result[:max_count]

    max_age_days: int | None = policy.get("max_age_days")
    if max_age_days is not None and max_age_days >= 0:
        cutoff = _utcnow().timestamp() - max_age_days * 86400
        kept = []
        for rec in result:
            ts_str = rec.get(timestamp_key, "")
            try:
                ts = _parse_iso(ts_str).timestamp()
            except (ValueError, TypeError):
                kept.append(rec)
                continue
            if ts >= cutoff:
                kept.append(rec)
        result = kept

    return result


def enforcement_summary(
    policy_path: str,
    job_id: str,
    original_count: int,
    surviving_count: int,
) -> str:
    """Return a human-readable summary of what the enforcer pruned."""
    pruned = original_count - surviving_count
    policy = get_retention_policy(policy_path, job_id)
    parts = []
    if "max_count" in policy:
        parts.append(f"max_count={policy['max_count']}")
    if "max_age_days" in policy:
        parts.append(f"max_age_days={policy['max_age_days']}")
    policy_str = ", ".join(parts) if parts else "none"
    return (
        f"job={job_id} policy=({policy_str}) "
        f"original={original_count} surviving={surviving_count} pruned={pruned}"
    )
