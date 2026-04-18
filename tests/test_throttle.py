"""Tests for cronwrap.throttle."""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from cronwrap.throttle import _parse_duration, should_throttle, throttle_reason


# --- _parse_duration ---

def test_parse_seconds():
    assert _parse_duration("30s") == timedelta(seconds=30)

def test_parse_minutes():
    assert _parse_duration("5m") == timedelta(minutes=5)

def test_parse_hours():
    assert _parse_duration("2h") == timedelta(hours=2)

def test_parse_days():
    assert _parse_duration("1d") == timedelta(days=1)

def test_parse_invalid():
    with pytest.raises(ValueError):
        _parse_duration("10x")


# --- should_throttle ---

@pytest.fixture()
def hist_file(tmp_path):
    return str(tmp_path / "history.json")


def _write_history(path: str, job_id: str, started_at: str):
    data = {job_id: [{"started_at": started_at, "exit_code": 0, "duration": 1.0}]}
    Path(path).write_text(json.dumps(data))


def test_no_history_no_throttle(hist_file):
    assert should_throttle("myjob", "10m", hist_file) is False


def test_recent_run_throttles(hist_file):
    recent = (datetime.utcnow() - timedelta(minutes=2)).isoformat()
    _write_history(hist_file, "myjob", recent)
    assert should_throttle("myjob", "10m", hist_file) is True


def test_old_run_no_throttle(hist_file):
    old = (datetime.utcnow() - timedelta(hours=2)).isoformat()
    _write_history(hist_file, "myjob", old)
    assert should_throttle("myjob", "30m", hist_file) is False


def test_different_job_no_throttle(hist_file):
    recent = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
    _write_history(hist_file, "otherjob", recent)
    assert should_throttle("myjob", "10m", hist_file) is False


# --- throttle_reason ---

def test_throttle_reason_no_history(hist_file):
    reason = throttle_reason("myjob", "5m", hist_file)
    assert "no previous run" in reason


def test_throttle_reason_with_history(hist_file):
    ts = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
    _write_history(hist_file, "myjob", ts)
    reason = throttle_reason("myjob", "5m", hist_file)
    assert "myjob" in reason
    assert "5m" in reason
