"""Generate human-readable reports from job metrics."""
from __future__ import annotations
from typing import Dict, List, Optional
from cronwrap.metrics import JobMetrics, load_metrics


def _bar(value: float, width: int = 20) -> str:
    filled = int(round(value * width))
    return "#" * filled + "-" * (width - filled)


def format_job_report(m: JobMetrics) -> str:
    lines = [
        f"Job: {m.job_id}",
        f"  Runs       : {m.total_runs}",
        f"  Successes  : {m.success_count}",
        f"  Failures   : {m.failure_count}",
    ]
    if m.success_rate is not None:
        pct = m.success_rate * 100
        lines.append(f"  Success %  : {pct:.1f}%  [{_bar(m.success_rate)}]")
    if m.avg_duration is not None:
        lines.append(f"  Avg Duration: {m.avg_duration:.3f}s")
    if m.durations:
        lines.append(f"  Last Duration: {m.durations[-1]:.3f}s")
    return "\n".join(lines)


def format_summary(metrics: Dict[str, JobMetrics]) -> str:
    if not metrics:
        return "No metrics recorded."
    parts = [format_job_report(m) for m in metrics.values()]
    return "\n\n".join(parts)


def print_report(path: str, job_id: Optional[str] = None) -> str:
    all_metrics = load_metrics(path)
    if job_id:
        m = all_metrics.get(job_id)
        if not m:
            return f"No metrics found for job: {job_id}"
        return format_job_report(m)
    return format_summary(all_metrics)
