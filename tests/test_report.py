"""Tests for cronwrap.report."""
import pytest
from cronwrap.metrics import JobMetrics, record_metric
from cronwrap.report import format_job_report, format_summary, print_report


@pytest.fixture
def metrics_file(tmp_path):
    return str(tmp_path / "metrics.json")


def make_metric(job_id="job1", runs=4, success=3, fail=1, total_dur=8.0):
    return JobMetrics(
        job_id=job_id,
        total_runs=runs,
        success_count=success,
        failure_count=fail,
        total_duration=total_dur,
        durations=[1.0, 2.0, 3.0, 2.0],
    )


def test_format_job_report_contains_job_id():
    m = make_metric()
    report = format_job_report(m)
    assert "job1" in report


def test_format_job_report_shows_counts():
    m = make_metric(runs=10, success=8, fail=2)
    report = format_job_report(m)
    assert "10" in report
    assert "8" in report
    assert "2" in report


def test_format_job_report_shows_success_rate():
    m = make_metric(runs=4, success=3, fail=1)
    report = format_job_report(m)
    assert "75.0%" in report


def test_format_job_report_shows_avg_duration():
    m = make_metric(runs=2, total_dur=4.0)
    report = format_job_report(m)
    assert "2.000s" in report


def test_format_summary_no_metrics():
    result = format_summary({})
    assert "No metrics" in result


def test_format_summary_multiple_jobs():
    metrics = {
        "a": make_metric("a"),
        "b": make_metric("b"),
    }
    result = format_summary(metrics)
    assert "Job: a" in result
    assert "Job: b" in result


def test_print_report_unknown_job(metrics_file):
    result = print_report(metrics_file, job_id="ghost")
    assert "No metrics" in result


def test_print_report_specific_job(metrics_file):
    record_metric(metrics_file, "myjob", success=True, duration=1.0)
    result = print_report(metrics_file, job_id="myjob")
    assert "myjob" in result


def test_print_report_all_jobs(metrics_file):
    record_metric(metrics_file, "alpha", success=True, duration=1.0)
    record_metric(metrics_file, "beta", success=False, duration=2.0)
    result = print_report(metrics_file)
    assert "alpha" in result
    assert "beta" in result
