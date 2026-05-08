"""Tests for cronwrap.tag_report."""

from __future__ import annotations

from cronwrap.metrics import JobMetrics
from cronwrap.tag_report import format_tag_report, format_tag_section, print_tag_report


def _make_metrics(tags: dict) -> JobMetrics:
    return JobMetrics(job_id="", tags=tags, runs=[], durations=[])


def test_format_tag_section_contains_tag_name():
    result = format_tag_section("production", ["job-a", "job-b"])
    assert "[production]" in result


def test_format_tag_section_lists_jobs():
    result = format_tag_section("staging", ["job-x"])
    assert "job-x" in result


def test_format_tag_section_sorts_jobs():
    result = format_tag_section("dev", ["zzz", "aaa"])
    lines = result.splitlines()
    job_lines = [l.strip() for l in lines if l.strip().startswith("-")]
    assert job_lines[0] == "- aaa"
    assert job_lines[1] == "- zzz"


def test_format_tag_report_header_present():
    metrics = {
        "job-1": _make_metrics({"env": "prod"}),
    }
    result = format_tag_report(metrics, tag_key="env")
    assert "Tag Report" in result
    assert "env" in result


def test_format_tag_report_groups_by_tag():
    metrics = {
        "job-a": _make_metrics({"env": "prod"}),
        "job-b": _make_metrics({"env": "staging"}),
        "job-c": _make_metrics({"env": "prod"}),
    }
    result = format_tag_report(metrics, tag_key="env")
    assert "[prod]" in result
    assert "[staging]" in result
    assert "job-a" in result
    assert "job-b" in result
    assert "job-c" in result


def test_format_tag_report_summary_counts():
    metrics = {
        "job-a": _make_metrics({"env": "prod"}),
        "job-b": _make_metrics({"env": "prod"}),
        "job-c": _make_metrics({"env": "dev"}),
    }
    result = format_tag_report(metrics, tag_key="env")
    assert "prod: 2 job(s)" in result
    assert "dev: 1 job(s)" in result


def test_format_tag_report_empty_metrics():
    result = format_tag_report({}, tag_key="env")
    assert "(no jobs)" in result


def test_format_tag_report_untagged_jobs_appear():
    metrics = {
        "job-x": _make_metrics({}),
    }
    result = format_tag_report(metrics, tag_key="env")
    assert "untagged" in result or "job-x" in result


def test_print_tag_report_outputs_text(capsys):
    metrics = {
        "job-1": _make_metrics({"env": "prod"}),
    }
    print_tag_report(metrics, tag_key="env")
    captured = capsys.readouterr()
    assert "Tag Report" in captured.out
    assert "prod" in captured.out
