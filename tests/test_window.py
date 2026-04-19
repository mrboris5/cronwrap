"""Tests for cronwrap.window."""

import pytest
from datetime import datetime, time

from cronwrap.window import _parse_time, parse_window, in_window, window_reason


def _dt(h: int, m: int) -> datetime:
    return datetime(2024, 1, 15, h, m, 0)


def test_parse_time_valid():
    assert _parse_time("09:30") == time(9, 30)


def test_parse_time_invalid_format():
    with pytest.raises(ValueError, match="Invalid time format"):
        _parse_time("9:5:0")


def test_parse_time_out_of_range():
    with pytest.raises(ValueError, match="out of range"):
        _parse_time("25:00")


def test_parse_window_returns_tuple():
    start, end = parse_window("08:00-17:00")
    assert start == time(8, 0)
    assert end == time(17, 0)


def test_parse_window_invalid():
    with pytest.raises(ValueError, match="Invalid window format"):
        parse_window("0800-1700")


def test_in_window_true():
    assert in_window("08:00-17:00", _dt(12, 0)) is True


def test_in_window_false():
    assert in_window("08:00-17:00", _dt(20, 0)) is False


def test_in_window_boundary_start():
    assert in_window("08:00-17:00", _dt(8, 0)) is True


def test_in_window_boundary_end():
    assert in_window("08:00-17:00", _dt(17, 0)) is True


def test_in_window_overnight_inside():
    assert in_window("22:00-06:00", _dt(23, 30)) is True


def test_in_window_overnight_early_morning():
    assert in_window("22:00-06:00", _dt(3, 0)) is True


def test_in_window_overnight_outside():
    assert in_window("22:00-06:00", _dt(12, 0)) is False


def test_window_reason_inside():
    reason = window_reason("08:00-17:00", _dt(10, 0))
    assert "within window" in reason
    assert "08:00-17:00" in reason


def test_window_reason_outside():
    reason = window_reason("08:00-17:00", _dt(20, 0))
    assert "outside window" in reason
    assert "20:00" in reason
