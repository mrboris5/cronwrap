"""Tests for cronwrap.digest."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta

import pytest

from cronwrap.digest import (
    _parse_hours,
    runs_in_window,
    digest_for_job,
    format_digest,
)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def hist_file(tmp_path):
    return str(tmp_path / "history.json")


def _write_history(path: str, job_id: str, entries: list) -> None:
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data[job_id] = entries
    with open(path, "w") as f:
        json.dump(data, f)


# --- _parse_hours ---

def test_parse_hours_h():
    assert _parse_hours("24h") == 24


def test_parse_hours_d():
    assert _parse_hours("2d") == 48


def test_parse_hours_plain_int():
    assert _parse_hours("12") == 12


# --- runs_in_window ---

def test_runs_in_window_empty_history(hist_file):
    result = runs_in_window(hist_file, "job1", 24)
    assert result == []


def test_runs_in_window_returns_recent(hist_file):
    now = _utcnow()
    entries = [
        {"timestamp": _iso(now - timedelta(hours=1)), "exit_code": 0, "duration": 1.0},
        {"timestamp": _iso(now - timedelta(hours=30)), "exit_code": 0, "duration": 2.0},
    ]
    _write_history(hist_file, "job1", entries)
    result = runs_in_window(hist_file, "job1", 24)
    assert len(result) == 1
    assert result[0]["duration"] == 1.0


def test_runs_in_window_all_old(hist_file):
    now = _utcnow()
    entries = [
        {"timestamp": _iso(now - timedelta(hours=50)), "exit_code": 0, "duration": 1.0},
    ]
    _write_history(hist_file, "job1", entries)
    assert runs_in_window(hist_file, "job1", 24) == []


# --- digest_for_job ---

def test_digest_for_job_no_runs(hist_file, tmp_path):
    metrics_path = str(tmp_path / "metrics.json")
    d = digest_for_job(hist_file, metrics_path, "job1", "24h")
    assert d["total_runs"] == 0
    assert d["success_rate"] == 0.0
    assert d["avg_duration"] == 0.0


def test_digest_for_job_counts(hist_file, tmp_path):
    metrics_path = str(tmp_path / "metrics.json")
    now = _utcnow()
    entries = [
        {"timestamp": _iso(now - timedelta(hours=1)), "exit_code": 0, "duration": 2.0},
        {"timestamp": _iso(now - timedelta(hours=2)), "exit_code": 1, "duration": 4.0},
        {"timestamp": _iso(now - timedelta(hours=3)), "exit_code": 0, "duration": 6.0},
    ]
    _write_history(hist_file, "myjob", entries)
    d = digest_for_job(hist_file, metrics_path, "myjob", "24h")
    assert d["total_runs"] == 3
    assert d["successes"] == 2
    assert d["failures"] == 1
    assert abs(d["success_rate"] - 2 / 3) < 0.001
    assert d["avg_duration"] == pytest.approx(4.0, rel=1e-3)


# --- format_digest ---

def test_format_digest_contains_job_id():
    d = {
        "job_id": "backup",
        "window": "24h",
        "total_runs": 5,
        "successes": 4,
        "failures": 1,
        "success_rate": 0.8,
        "avg_duration": 3.5,
    }
    out = format_digest(d)
    assert "backup" in out
    assert "24h" in out
    assert "80.0%" in out
