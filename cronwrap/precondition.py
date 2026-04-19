"""Precondition checks before running a job (dependencies + circuit + throttle)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.dependency import check_dependencies, dependency_reason
from cronwrap.circuit import is_open
from cronwrap.throttle import should_throttle, throttle_reason


@dataclass
class PreconditionResult:
    allowed: bool
    reasons: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.allowed:
            return "OK"
        return "; ".join(self.reasons)


def check_preconditions(
    job_id: str,
    *,
    history_file: Optional[str] = None,
    dep_job_ids: Optional[List[str]] = None,
    dep_max_age_seconds: Optional[float] = None,
    circuit_state_file: Optional[str] = None,
    circuit_threshold: int = 3,
    circuit_reset_seconds: float = 300,
    last_run_timestamp: Optional[str] = None,
    min_interval: Optional[str] = None,
) -> PreconditionResult:
    """Run all precondition checks and return a combined result."""
    reasons: List[str] = []

    # Dependency check
    if dep_job_ids and history_file:
        unmet = check_dependencies(dep_job_ids, history_file, dep_max_age_seconds)
        if unmet:
            reasons.append(dependency_reason(unmet))

    # Circuit breaker check
    if circuit_state_file:
        if is_open(job_id, circuit_state_file, circuit_threshold, circuit_reset_seconds):
            reasons.append(f"Circuit open for job '{job_id}'")

    # Throttle check
    if last_run_timestamp and min_interval:
        if should_throttle(last_run_timestamp, min_interval):
            reasons.append(throttle_reason(last_run_timestamp, min_interval))

    return PreconditionResult(allowed=len(reasons) == 0, reasons=reasons)
