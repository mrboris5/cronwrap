"""Tests for cronwrap.drift."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from cronwrap.drift import (
    load_drift,
    save_drift,
    record_drift,
    drift_stats,
    last_drift,
)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


@pytest.fixture()
def dfile(tmp_path: Path) -> str:
    return str(tmp_path / "drift.json")


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_drift_missing_file(dfile):
    assert load_drift(dfile) == {}


def test_load_drift_corrupt_file(dfile):
    Path(dfile).write_text("not json")
    assert load_drift(dfile) == {}


def test_save_and_load_roundtrip(dfile):
    payload = {"job1": [{"drift_seconds": 5.0}]}
    save_drift(dfile, payload)
    assert load_drift(dfile) == payload


# ---------------------------------------------------------------------------
# record_drift
# ---------------------------------------------------------------------------

def test_record_drift_creates_entry(dfile):
    now = datetime.now(timezone.utc)
    expected = now - timedelta(seconds=10)
    entry = record_drift(dfile, "backup", _iso(expected), _iso(now))
    assert entry["job_id"] == "backup"
    assert abs(entry["drift_seconds"] - 10.0) < 0.1


def test_record_drift_negative_drift(dfile):
    now = datetime.now(timezone.utc)
    expected = now + timedelta(seconds=30)
    entry = record_drift(dfile, "backup", _iso(expected), _iso(now))
    assert entry["drift_seconds"] < 0


def test_record_drift_uses_now_when_actual_omitted(dfile):
    expected = datetime.now(timezone.utc) - timedelta(seconds=5)
    entry = record_drift(dfile, "job1", _iso(expected))
    assert entry["drift_seconds"] >= 4.9


def test_record_drift_persists(dfile):
    base = datetime.now(timezone.utc)
    record_drift(dfile, "j", _iso(base - timedelta(seconds=1)), _iso(base))
    record_drift(dfile, "j", _iso(base - timedelta(seconds=2)), _iso(base))
    data = load_drift(dfile)
    assert len(data["j"]) == 2


def test_record_drift_trims_to_max(dfile, monkeypatch):
    import cronwrap.drift as mod
    monkeypatch.setattr(mod, "_MAX_ENTRIES", 3)
    base = datetime.now(timezone.utc)
    for i in range(5):
        record_drift(dfile, "j", _iso(base - timedelta(seconds=i)), _iso(base))
    data = load_drift(dfile)
    assert len(data["j"]) == 3


# ---------------------------------------------------------------------------
# drift_stats
# ---------------------------------------------------------------------------

def test_drift_stats_no_data(dfile):
    stats = drift_stats(dfile, "missing")
    assert stats["count"] == 0
    assert stats["mean_seconds"] is None


def test_drift_stats_values(dfile):
    base = datetime.now(timezone.utc)
    record_drift(dfile, "j", _iso(base - timedelta(seconds=10)), _iso(base))
    record_drift(dfile, "j", _iso(base - timedelta(seconds=20)), _iso(base))
    stats = drift_stats(dfile, "j")
    assert stats["count"] == 2
    assert abs(stats["mean_seconds"] - 15.0) < 0.5
    assert abs(stats["max_seconds"] - 20.0) < 0.5


# ---------------------------------------------------------------------------
# last_drift
# ---------------------------------------------------------------------------

def test_last_drift_none_when_empty(dfile):
    assert last_drift(dfile, "x") is None


def test_last_drift_returns_most_recent(dfile):
    base = datetime.now(timezone.utc)
    record_drift(dfile, "j", _iso(base - timedelta(seconds=5)), _iso(base))
    record_drift(dfile, "j", _iso(base - timedelta(seconds=99)), _iso(base))
    entry = last_drift(dfile, "j")
    assert abs(entry["drift_seconds"] - 99.0) < 0.5
