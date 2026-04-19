"""Spread execution: combine schedule awareness with jitter to avoid thundering herd."""
from typing import Optional
from cronwrap.jitter import apply_jitter, jitter_reason, _parse_seconds
from cronwrap.logger import get_logger

logger = get_logger(__name__)


def spread_delay(
    max_jitter: Optional[str],
    job_id: str = "job",
    dry_run: bool = False,
) -> float:
    """Apply jitter delay if configured. Returns seconds slept (0 if disabled)."""
    if not max_jitter:
        logger.debug("[%s] No jitter configured, running immediately.", job_id)
        return 0.0
    slept = apply_jitter(max_jitter, dry_run=dry_run)
    reason = jitter_reason(max_jitter, slept=slept)
    logger.info("[%s] %s", job_id, reason)
    return slept


def spread_summary(max_jitter: Optional[str]) -> str:
    """Return a human-readable summary of the spread configuration."""
    if not max_jitter:
        return "Spread/jitter: disabled."
    seconds = _parse_seconds(max_jitter)
    return f"Spread/jitter: up to {seconds:.1f}s random delay before execution."
