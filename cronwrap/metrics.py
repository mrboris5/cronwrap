"""Simple metrics collection for job runs."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class JobMetrics:
    job_id: str
    total_runs: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration: float = 0.0
    durations: List[float] = field(default_factory=list)

    @property
    def avg_duration(self) -> Optional[float]:
        return self.total_duration / self.total_runs if self.total_runs else None

    @property
    def success_rate(self) -> Optional[float]:
        return self.success_count / self.total_runs if self.total_runs else None


def load_metrics(path: str) -> Dict[str, JobMetrics]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            raw = json.load(f)
        result = {}
        for job_id, data in raw.items():
            m = JobMetrics(job_id=job_id, **{k: v for k, v in data.items() if k != 'job_id'})
            result[job_id] = m
        return result
    except (json.JSONDecodeError, TypeError, KeyError):
        return {}


def save_metrics(path: str, metrics: Dict[str, JobMetrics]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {}
    for job_id, m in metrics.items():
        data[job_id] = {
            "total_runs": m.total_runs,
            "success_count": m.success_count,
            "failure_count": m.failure_count,
            "total_duration": m.total_duration,
            "durations": m.durations[-100:],
        }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def record_metric(path: str, job_id: str, success: bool, duration: float) -> JobMetrics:
    all_metrics = load_metrics(path)
    m = all_metrics.get(job_id, JobMetrics(job_id=job_id))
    m.total_runs += 1
    m.total_duration += duration
    m.durations.append(round(duration, 3))
    if success:
        m.success_count += 1
    else:
        m.failure_count += 1
    all_metrics[job_id] = m
    save_metrics(path, all_metrics)
    return m


def get_metrics(path: str, job_id: str) -> Optional[JobMetrics]:
    return load_metrics(path).get(job_id)
