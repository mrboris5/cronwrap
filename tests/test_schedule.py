"""Tests for cronwrap.schedule."""

import pytest
from datetime import datetime
from cronwrap.schedule import is_due, describe, _match_field


# --- _match_field ---

def test_match_field_wildcard():
    assert _match_field(30, "*", 0, 59) is True

def test_match_field_exact():
    assert _match_field(5, "5", 0, 59) is True
    assert _match_field(6, "5", 0, 59) is False

def test_match_field_step():
    assert _match_field(0, "*/15", 0, 59) is True
    assert _match_field(15, "*/15", 0, 59) is True
    assert _match_field(7, "*/15", 0, 59) is False

def test_match_field_range():
    assert _match_field(3, "1-5", 0, 59) is True
    assert _match_field(6, "1-5", 0, 59) is False

def test_match_field_list():
    assert _match_field(2, "1,2,3", 0, 59) is True
    assert _match_field(5, "1,2,3", 0, 59) is False


# --- is_due ---

def test_is_due_every_minute():
    dt = datetime(2024, 6, 1, 12, 30)  # Saturday, weekday=5
    assert is_due("* * * * *", at=dt) is True

def test_is_due_exact_match():
    dt = datetime(2024, 6, 1, 12, 30)
    assert is_due("30 12 1 6 *", at=dt) is True

def test_is_due_no_match():
    dt = datetime(2024, 6, 1, 12, 30)
    assert is_due("0 9 * * *", at=dt) is False

def test_is_due_weekday_match():
    dt = datetime(2024, 6, 3, 8, 0)  # Monday, weekday=0
    assert is_due("0 8 * * 0", at=dt) is True

def test_is_due_weekday_no_match():
    dt = datetime(2024, 6, 1, 8, 0)  # Saturday, weekday=5
    assert is_due("0 8 * * 0", at=dt) is False

def test_is_due_step_minutes():
    dt = datetime(2024, 1, 1, 0, 30)
    assert is_due("*/30 * * * *", at=dt) is True
    dt2 = datetime(2024, 1, 1, 0, 7)
    assert is_due("*/30 * * * *", at=dt2) is False

def test_is_due_invalid_expr():
    with pytest.raises(ValueError):
        is_due("* * *", at=datetime.now())

def test_is_due_uses_now_by_default():
    # Should not raise
    result = is_due("* * * * *")
    assert result is True


# --- describe ---

def test_describe_basic():
    desc = describe("30 12 * * 1")
    assert "minute=30" in desc
    assert "hour=12" in desc
    assert "weekday=1" in desc

def test_describe_invalid():
    with pytest.raises(ValueError):
        describe("bad expr")
