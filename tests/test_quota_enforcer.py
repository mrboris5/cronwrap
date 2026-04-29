"""Tests for cronwrap.quota_enforcer."""

from datetime import datetime, timedelta, timezone

import pytest

from cronwrap.quota_enforcer import (
    _parse_period,
    is_quota_exceeded,
    quota_exceeded_reason,
    runs_in_period,
)
from cronwrap.quota_policy import set_quota


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- _parse_period ---

def test_parse_period_hours():
    assert _parse_period("2h") == timedelta(hours=2)


def test_parse_period_days():
    assert _parse_period("7d") == timedelta(days=7)


def test_parse_period_minutes():
    assert _parse_period("30m") == timedelta(minutes=30)


def test_parse_period_seconds():
    assert _parse_period("60s") == timedelta(seconds=60)


def test_parse_period_invalid():
    with pytest.raises(ValueError):
        _parse_period("bad")


# --- runs_in_period ---

def test_runs_in_period_all_recent():
    now = _utcnow()
    history = [{"timestamp": _iso(now - timedelta(minutes=5))} for _ in range(3)]
    assert runs_in_period(history, "1h") == 3


def test_runs_in_period_some_old():
    now = _utcnow()
    history = [
        {"timestamp": _iso(now - timedelta(hours=2))},
        {"timestamp": _iso(now - timedelta(minutes=10))},
        {"timestamp": _iso(now - timedelta(minutes=1))},
    ]
    assert runs_in_period(history, "1h") == 2


def test_runs_in_period_empty():
    assert runs_in_period([], "1h") == 0


def test_runs_in_period_bad_timestamp():
    history = [{"timestamp": "not-a-date"}]
    assert runs_in_period(history, "1h") == 0


# --- is_quota_exceeded ---

def test_is_quota_exceeded_no_policy(tmp_path):
    qp = str(tmp_path / "qp.json")
    history = [{"timestamp": _iso(_utcnow())} for _ in range(10)]
    assert is_quota_exceeded("job1", history, policy_path=qp) is False


def test_is_quota_exceeded_under_limit(tmp_path):
    qp = str(tmp_path / "qp.json")
    set_quota("job1", 5, "1h", path=qp)
    now = _utcnow()
    history = [{"timestamp": _iso(now - timedelta(minutes=i))} for i in range(3)]
    assert is_quota_exceeded("job1", history, policy_path=qp) is False


def test_is_quota_exceeded_at_limit(tmp_path):
    qp = str(tmp_path / "qp.json")
    set_quota("job1", 3, "1h", path=qp)
    now = _utcnow()
    history = [{"timestamp": _iso(now - timedelta(minutes=i))} for i in range(3)]
    assert is_quota_exceeded("job1", history, policy_path=qp) is True


def test_quota_exceeded_reason_returns_string(tmp_path):
    qp = str(tmp_path / "qp.json")
    set_quota("job1", 2, "1h", path=qp)
    now = _utcnow()
    history = [{"timestamp": _iso(now - timedelta(minutes=i))} for i in range(3)]
    reason = quota_exceeded_reason("job1", history, policy_path=qp)
    assert "job1" in reason
    assert "3/2" in reason


def test_quota_exceeded_reason_empty_when_ok(tmp_path):
    qp = str(tmp_path / "qp.json")
    set_quota("job1", 10, "1h", path=qp)
    history = [{"timestamp": _iso(_utcnow())}]
    reason = quota_exceeded_reason("job1", history, policy_path=qp)
    assert reason == ""
