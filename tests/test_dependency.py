"""Tests for cronwrap.dependency."""
import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from cronwrap.dependency import (
    last_success,
    dependency_met,
    check_dependencies,
    dependency_reason,
)


@pytest.fixture
def hist_file(tmp_path):
    return str(tmp_path / "history.json")


def _write(hist_file, entries):
    Path(hist_file).write_text(json.dumps(entries))


def _iso(dt):
    return dt.isoformat()


def now():
    return datetime.now(timezone.utc)


def test_last_success_no_file(hist_file):
    assert last_success("job1", hist_file) is None


def test_last_success_no_matching_entry(hist_file):
    _write(hist_file, [{"job_id": "other", "exit_code": 0, "timestamp": _iso(now())}])
    assert last_success("job1", hist_file) is None


def test_last_success_failed_entry(hist_file):
    _write(hist_file, [{"job_id": "job1", "exit_code": 1, "timestamp": _iso(now())}])
    assert last_success("job1", hist_file) is None


def test_last_success_returns_datetime(hist_file):
    ts = now()
    _write(hist_file, [{"job_id": "job1", "exit_code": 0, "timestamp": _iso(ts)}])
    result = last_success("job1", hist_file)
    assert result is not None
    assert abs((result - ts).total_seconds()) < 1


def test_dependency_met_no_history(hist_file):
    assert dependency_met("job1", hist_file) is False


def test_dependency_met_success(hist_file):
    _write(hist_file, [{"job_id": "job1", "exit_code": 0, "timestamp": _iso(now())}])
    assert dependency_met("job1", hist_file) is True


def test_dependency_met_too_old(hist_file):
    old = now() - timedelta(seconds=3600)
    _write(hist_file, [{"job_id": "job1", "exit_code": 0, "timestamp": _iso(old)}])
    assert dependency_met("job1", hist_file, max_age_seconds=60) is False


def test_dependency_met_within_age(hist_file):
    recent = now() - timedelta(seconds=30)
    _write(hist_file, [{"job_id": "job1", "exit_code": 0, "timestamp": _iso(recent)}])
    assert dependency_met("job1", hist_file, max_age_seconds=60) is True


def test_check_dependencies_all_met(hist_file):
    ts = _iso(now())
    _write(hist_file, [
        {"job_id": "a", "exit_code": 0, "timestamp": ts},
        {"job_id": "b", "exit_code": 0, "timestamp": ts},
    ])
    assert check_dependencies(["a", "b"], hist_file) == []


def test_check_dependencies_some_unmet(hist_file):
    _write(hist_file, [{"job_id": "a", "exit_code": 0, "timestamp": _iso(now())}])
    unmet = check_dependencies(["a", "b"], hist_file)
    assert unmet == ["b"]


def test_dependency_reason_empty():
    assert dependency_reason([]) == ""


def test_dependency_reason_message():
    msg = dependency_reason(["job1", "job2"])
    assert "job1" in msg
    assert "job2" in msg
    assert "Unmet" in msg
