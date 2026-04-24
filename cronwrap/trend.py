"""Trend analysis for job duration and success rate over time."""

from __future__ import annotations

from typing import List, Optional

from cronwrap.metrics import JobMetrics, load_metrics


def _slope(values: List[float]) -> float:
    """Return simple linear regression slope for a sequence of values."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def duration_trend(metrics: JobMetrics) -> Optional[str]:
    """Return 'improving', 'degrading', or 'stable' based on recent durations.

    Returns None if there is insufficient data.
    """
    durations = metrics.get("durations", [])
    if len(durations) < 3:
        return None
    slope = _slope(durations[-10:])
    if slope > 0.5:
        return "degrading"
    if slope < -0.5:
        return "improving"
    return "stable"


def success_trend(metrics: JobMetrics) -> Optional[str]:
    """Return 'improving', 'degrading', or 'stable' based on recent outcomes.

    Each outcome is 1 (success) or 0 (failure).
    Returns None if there is insufficient data.
    """
    outcomes = metrics.get("outcomes", [])
    if len(outcomes) < 3:
        return None
    slope = _slope(outcomes[-10:])
    if slope > 0.05:
        return "improving"
    if slope < -0.05:
        return "degrading"
    return "stable"


def trend_summary(job_id: str, metrics_file: str) -> dict:
    """Return a dict with duration_trend and success_trend for *job_id*."""
    all_metrics = load_metrics(metrics_file)
    metrics = all_metrics.get(job_id, {})
    return {
        "job_id": job_id,
        "duration_trend": duration_trend(metrics),
        "success_trend": success_trend(metrics),
    }
