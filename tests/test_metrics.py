"""Tests for cronwrap.metrics."""
import json
import os
import pytest
from cronwrap.metrics import (
    JobMetrics,
    load_metrics,
    save_metrics,
    record_metric,
    get_metrics,
)


@pytest.fixture
def metrics_file(tmp_path):
    return str(tmp_path / "metrics.json")


def test_load_metrics_missing_file(metrics_file):
    assert load_metrics(metrics_file) == {}


def test_load_metrics_corrupt_file(metrics_file):
    with open(metrics_file, "w") as f:
        f.write("not json")
    assert load_metrics(metrics_file) == {}


def test_save_and_load_roundtrip(metrics_file):
    m = JobMetrics(job_id="job1", total_runs=3, success_count=2, failure_count=1,
                   total_duration=9.0, durations=[2.0, 3.0, 4.0])
    save_metrics(metrics_file, {"job1": m})
    loaded = load_metrics(metrics_file)
    assert "job1" in loaded
    assert loaded["job1"].total_runs == 3
    assert loaded["job1"].success_count == 2


def test_record_metric_success(metrics_file):
    m = record_metric(metrics_file, "myjob", success=True, duration=1.5)
    assert m.total_runs == 1
    assert m.success_count == 1
    assert m.failure_count == 0
    assert m.total_duration == pytest.approx(1.5)


def test_record_metric_failure(metrics_file):
    record_metric(metrics_file, "myjob", success=False, duration=2.0)
    m = record_metric(metrics_file, "myjob", success=False, duration=3.0)
    assert m.total_runs == 2
    assert m.failure_count == 2
    assert m.success_count == 0


def test_record_metric_accumulates(metrics_file):
    record_metric(metrics_file, "j", success=True, duration=1.0)
    record_metric(metrics_file, "j", success=False, duration=2.0)
    m = record_metric(metrics_file, "j", success=True, duration=3.0)
    assert m.total_runs == 3
    assert m.success_count == 2
    assert m.failure_count == 1
    assert m.avg_duration == pytest.approx(2.0)


def test_success_rate(metrics_file):
    record_metric(metrics_file, "j", success=True, duration=1.0)
    record_metric(metrics_file, "j", success=True, duration=1.0)
    m = record_metric(metrics_file, "j", success=False, duration=1.0)
    assert m.success_rate == pytest.approx(2 / 3)


def test_avg_duration_none_when_no_runs():
    m = JobMetrics(job_id="x")
    assert m.avg_duration is None
    assert m.success_rate is None


def test_get_metrics_returns_none_for_unknown(metrics_file):
    assert get_metrics(metrics_file, "nope") is None


def test_get_metrics_returns_data(metrics_file):
    record_metric(metrics_file, "k", success=True, duration=5.0)
    m = get_metrics(metrics_file, "k")
    assert m is not None
    assert m.job_id == "k"
