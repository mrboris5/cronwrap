"""Tests for cronwrap.cooldown."""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from cronwrap.cooldown import _parse_seconds, is_cooling_down, cooldown_reason


# --- _parse_seconds ---

def test_parse_seconds_s():
    assert _parse_seconds("30s") == 30

def test_parse_seconds_m():
    assert _parse_seconds("5m") == 300

def test_parse_seconds_h():
    assert _parse_seconds("2h") == 7200

def test_parse_seconds_d():
    assert _parse_seconds("1d") == 86400

def test_parse_seconds_invalid():
    with pytest.raises(ValueError):
        _parse_seconds("10x")


# --- helpers ---

def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _write(path, job_id, entries):
    data = {job_id: entries}
    with open(path, "w") as f:
        json.dump(data, f)


@pytest.fixture
def hist_file(tmp_path):
    return str(tmp_path / "history.json")


now = datetime.now(timezone.utc)


# --- is_cooling_down ---

def test_no_history_not_cooling(hist_file):
    assert is_cooling_down("job1", "10m", hist_file) is False

def test_recent_run_is_cooling(hist_file):
    recent = _iso(now - timedelta(seconds=30))
    _write(hist_file, "job1", [{"finished_at": recent, "success": True}])
    assert is_cooling_down("job1", "5m", hist_file) is True

def test_old_run_not_cooling(hist_file):
    old = _iso(now - timedelta(hours=2))
    _write(hist_file, "job1", [{"finished_at": old, "success": True}])
    assert is_cooling_down("job1", "1h", hist_file) is False

def test_only_on_success_skips_failed_run(hist_file):
    recent = _iso(now - timedelta(seconds=30))
    _write(hist_file, "job1", [{"finished_at": recent, "success": False}])
    assert is_cooling_down("job1", "5m", hist_file, only_on_success=True) is False

def test_only_on_success_blocks_on_success(hist_file):
    recent = _iso(now - timedelta(seconds=30))
    _write(hist_file, "job1", [{"finished_at": recent, "success": True}])
    assert is_cooling_down("job1", "5m", hist_file, only_on_success=True) is True


# --- cooldown_reason ---

def test_cooldown_reason_returns_none_when_not_cooling(hist_file):
    assert cooldown_reason("job1", "5m", hist_file) is None

def test_cooldown_reason_returns_string_when_cooling(hist_file):
    recent = _iso(now - timedelta(seconds=10))
    _write(hist_file, "job1", [{"finished_at": recent, "success": True}])
    reason = cooldown_reason("job1", "5m", hist_file)
    assert reason is not None
    assert "job1" in reason
    assert "5m" in reason
