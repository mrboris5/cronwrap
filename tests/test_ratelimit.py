"""Tests for cronwrap.ratelimit."""

from __future__ import annotations

import json
import os
import time
import pytest

from cronwrap.ratelimit import (
    _parse_window,
    runs_in_window,
    is_rate_limited,
    rate_limit_reason,
)


def _iso(offset_seconds: int = 0) -> str:
    t = time.gmtime(time.time() + offset_seconds)
    return time.strftime("%Y-%m-%dT%H:%M:%S", t)


@pytest.fixture
def hist_file(tmp_path):
    return str(tmp_path / "history.json")


def _write_history(path, job_id, entries):
    data = {job_id: entries}
    with open(path, "w") as f:
        json.dump(data, f)


def test_parse_window_seconds():
    assert _parse_window("60s") == 60


def test_parse_window_minutes():
    assert _parse_window("5m") == 300


def test_parse_window_hours():
    assert _parse_window("2h") == 7200


def test_parse_window_days():
    assert _parse_window("1d") == 86400


def test_parse_window_invalid():
    with pytest.raises(ValueError):
        _parse_window("10x")


def test_runs_in_window_recent(hist_file):
    entries = [{"started_at": _iso(-30), "exit_code": 0}]
    _write_history(hist_file, "job1", entries)
    result = runs_in_window(hist_file, "job1", "5m")
    assert len(result) == 1


def test_runs_in_window_old_excluded(hist_file):
    entries = [{"started_at": _iso(-7200), "exit_code": 0}]
    _write_history(hist_file, "job1", entries)
    result = runs_in_window(hist_file, "job1", "1h")
    assert len(result) == 0


def test_is_rate_limited_true(hist_file):
    entries = [
        {"started_at": _iso(-10), "exit_code": 0},
        {"started_at": _iso(-20), "exit_code": 0},
        {"started_at": _iso(-30), "exit_code": 0},
    ]
    _write_history(hist_file, "job1", entries)
    assert is_rate_limited(hist_file, "job1", max_runs=3, window="1h") is True


def test_is_rate_limited_false(hist_file):
    entries = [{"started_at": _iso(-10), "exit_code": 0}]
    _write_history(hist_file, "job1", entries)
    assert is_rate_limited(hist_file, "job1", max_runs=5, window="1h") is False


def test_rate_limit_reason_contains_job(hist_file):
    _write_history(hist_file, "myjob", [])
    reason = rate_limit_reason(hist_file, "myjob", max_runs=3, window="1h")
    assert "myjob" in reason
    assert "1h" in reason
    assert "3" in reason
