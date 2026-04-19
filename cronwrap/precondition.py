"""Precondition checks: aggregate gate checks before running a job."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.throttle import should_throttle, throttle_reason
from cronwrap.ratelimit import is_rate_limited, rate_limit_reason
from cronwrap.circuit import is_open as circuit_is_open
from cronwrap.dependency import check_dependencies, dependency_reason
from cronwrap.cooldown import is_cooling_down, cooldown_reason


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
    throttle: Optional[str] = None,
    rate_limit: Optional[str] = None,
    circuit_state_file: Optional[str] = None,
    circuit_threshold: int = 3,
    dependencies: Optional[List[str]] = None,
    dep_max_age: Optional[str] = None,
    cooldown: Optional[str] = None,
    cooldown_success_only: bool = False,
) -> PreconditionResult:
    reasons: List[str] = []

    if throttle and history_file:
        if should_throttle(job_id, throttle, history_file):
            r = throttle_reason(job_id, throttle, history_file)
            if r:
                reasons.append(r)

    if rate_limit and history_file:
        if is_rate_limited(job_id, rate_limit, history_file):
            r = rate_limit_reason(job_id, rate_limit, history_file)
            if r:
                reasons.append(r)

    if circuit_state_file:
        if circuit_is_open(job_id, circuit_state_file, threshold=circuit_threshold):
            reasons.append(f"Circuit breaker open for '{job_id}'")

    if dependencies and history_file:
        unmet = check_dependencies(dependencies, history_file, max_age=dep_max_age)
        for dep in unmet:
            r = dependency_reason(dep, history_file, max_age=dep_max_age)
            if r:
                reasons.append(r)

    if cooldown and history_file:
        if is_cooling_down(job_id, cooldown, history_file, only_on_success=cooldown_success_only):
            r = cooldown_reason(job_id, cooldown, history_file, only_on_success=cooldown_success_only)
            if r:
                reasons.append(r)

    return PreconditionResult(allowed=len(reasons) == 0, reasons=reasons)
