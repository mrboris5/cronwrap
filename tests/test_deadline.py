"""Tests for cronwrap.deadline."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from cronwrap.deadline import (
    _parse_seconds,
    is_past_deadline,
    deadline_reason,
    check_deadline,
)


def _utc(**kwargs) -> datetime:
    return datetime.now(timezone.utc) - timedelta(**kwargs)


# --- _parse_seconds ---

def test_parse_seconds_s():
    assert _parse_seconds("45s") == 45


def test_parse_seconds_m():
    assert _parse_seconds("10m") == 600


def test_parse_seconds_h():
    assert _parse_seconds("2h") == 7200


def test_parse_seconds_d():
    assert _parse_seconds("1d") == 86400


def test_parse_seconds_invalid():
    with pytest.raises(ValueError, match="Invalid duration"):
        _parse_seconds("5x")


def test_parse_seconds_no_unit():
    with pytest.raises(ValueError):
        _parse_seconds("120")


# --- is_past_deadline ---

def test_is_past_deadline_within():
    scheduled = _utc(seconds=20)
    assert is_past_deadline(scheduled, "30s") is False


def test_is_past_deadline_exceeded():
    scheduled = _utc(seconds=60)
    assert is_past_deadline(scheduled, "30s") is True


def test_is_past_deadline_exactly_at_boundary():
    now = datetime.now(timezone.utc)
    scheduled = now - timedelta(seconds=30)
    # elapsed == max_seconds, not strictly greater
    assert is_past_deadline(scheduled, "30s", now=now) is False


def test_is_past_deadline_one_second_over():
    now = datetime.now(timezone.utc)
    scheduled = now - timedelta(seconds=31)
    assert is_past_deadline(scheduled, "30s", now=now) is True


# --- deadline_reason ---

def test_deadline_reason_contains_job_id():
    scheduled = _utc(seconds=120)
    reason = deadline_reason("my-job", scheduled, "1m")
    assert "my-job" in reason


def test_deadline_reason_contains_deadline():
    scheduled = _utc(seconds=120)
    reason = deadline_reason("job", scheduled, "1m")
    assert "1m" in reason
    assert "60s" in reason


def test_deadline_reason_contains_elapsed():
    now = datetime.now(timezone.utc)
    scheduled = now - timedelta(seconds=90)
    reason = deadline_reason("job", scheduled, "1m", now=now)
    assert "90s" in reason


# --- check_deadline ---

def test_check_deadline_no_deadline_returns_allowed():
    blocked, reason = check_deadline("job", _utc(seconds=999), None)
    assert blocked is False
    assert reason == ""


def test_check_deadline_no_scheduled_at_returns_allowed():
    blocked, reason = check_deadline("job", None, "5m")
    assert blocked is False


def test_check_deadline_within_window():
    scheduled = _utc(seconds=10)
    blocked, reason = check_deadline("job", scheduled, "1m")
    assert blocked is False
    assert reason == ""


def test_check_deadline_past_window():
    scheduled = _utc(minutes=10)
    blocked, reason = check_deadline("job", scheduled, "5m")
    assert blocked is True
    assert "job" in reason
