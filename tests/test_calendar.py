"""Tests for cronwrap.calendar."""

import pytest
from datetime import date

from cronwrap.calendar import (
    _parse_date,
    _parse_weekday,
    is_blocked_date,
    is_blocked_weekday,
    calendar_blocked,
    calendar_reason,
)

# 2024-01-15 is a Monday (weekday=0)
MONDAY = date(2024, 1, 15)
SATURDAY = date(2024, 1, 20)


def test_parse_date_valid():
    assert _parse_date("2024-01-15") == date(2024, 1, 15)


def test_parse_date_invalid():
    with pytest.raises(ValueError, match="Invalid date"):
        _parse_date("15-01-2024")


def test_parse_weekday_valid():
    assert _parse_weekday("mon") == 0
    assert _parse_weekday("sun") == 6


def test_parse_weekday_invalid():
    with pytest.raises(ValueError, match="Unknown weekday"):
        _parse_weekday("monday")


def test_is_blocked_date_match():
    assert is_blocked_date(["2024-01-15", "2024-12-25"], MONDAY) is True


def test_is_blocked_date_no_match():
    assert is_blocked_date(["2024-12-25"], MONDAY) is False


def test_is_blocked_date_empty():
    assert is_blocked_date([], MONDAY) is False


def test_is_blocked_weekday_match():
    assert is_blocked_weekday(["mon", "fri"], MONDAY) is True


def test_is_blocked_weekday_no_match():
    assert is_blocked_weekday(["sat", "sun"], MONDAY) is False


def test_calendar_blocked_by_date():
    assert calendar_blocked(blocked_dates=["2024-01-15"], now=MONDAY) is True


def test_calendar_blocked_by_weekday():
    assert calendar_blocked(blocked_weekdays=["sat"], now=SATURDAY) is True


def test_calendar_not_blocked():
    assert calendar_blocked(
        blocked_dates=["2024-12-25"], blocked_weekdays=["sun"], now=MONDAY
    ) is False


def test_calendar_blocked_none_args():
    assert calendar_blocked(now=MONDAY) is False


def test_calendar_reason_blocked_date():
    reason = calendar_reason(blocked_dates=["2024-01-15"], now=MONDAY)
    assert "blocked date" in reason
    assert "2024-01-15" in reason


def test_calendar_reason_blocked_weekday():
    reason = calendar_reason(blocked_weekdays=["sat"], now=SATURDAY)
    assert "blocked weekday" in reason
    assert "sat" in reason


def test_calendar_reason_not_blocked():
    reason = calendar_reason(now=MONDAY)
    assert "not blocked" in reason
