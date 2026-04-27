"""Tests for cronwrap.forecast."""

from datetime import datetime, timezone

import pytest

from cronwrap.forecast import forecast_summary, next_runs


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# next_runs
# ---------------------------------------------------------------------------

def test_next_runs_returns_correct_count():
    after = _utc(2024, 1, 1, 0, 0)
    # Every minute
    runs = next_runs("* * * * *", count=3, after=after)
    assert len(runs) == 3


def test_next_runs_every_minute_are_consecutive():
    after = _utc(2024, 1, 1, 12, 0)
    runs = next_runs("* * * * *", count=3, after=after)
    for i in range(1, len(runs)):
        delta = (runs[i] - runs[i - 1]).total_seconds()
        assert delta == 60


def test_next_runs_hourly():
    after = _utc(2024, 3, 15, 9, 0)
    runs = next_runs("0 * * * *", count=3, after=after)
    assert len(runs) == 3
    for dt in runs:
        assert dt.minute == 0


def test_next_runs_specific_hour_and_minute():
    after = _utc(2024, 6, 1, 0, 0)
    runs = next_runs("30 14 * * *", count=2, after=after)
    for dt in runs:
        assert dt.hour == 14
        assert dt.minute == 30


def test_next_runs_after_is_exclusive():
    """The 'after' time itself should not be included."""
    after = _utc(2024, 1, 1, 0, 0)
    runs = next_runs("* * * * *", count=1, after=after)
    assert runs[0] > after


def test_next_runs_returns_utc_aware():
    after = _utc(2024, 1, 1, 0, 0)
    runs = next_runs("* * * * *", count=1, after=after)
    assert runs[0].tzinfo is not None


def test_next_runs_invalid_count_raises():
    with pytest.raises(ValueError, match="count must be >= 1"):
        next_runs("* * * * *", count=0)


def test_next_runs_default_count():
    after = _utc(2024, 1, 1, 0, 0)
    runs = next_runs("* * * * *", after=after)
    assert len(runs) == 5


# ---------------------------------------------------------------------------
# forecast_summary
# ---------------------------------------------------------------------------

def test_forecast_summary_contains_expression():
    after = _utc(2024, 1, 1, 0, 0)
    summary = forecast_summary("0 * * * *", count=2, after=after)
    assert "0 * * * *" in summary


def test_forecast_summary_line_count():
    after = _utc(2024, 1, 1, 0, 0)
    summary = forecast_summary("* * * * *", count=3, after=after)
    # Header line + 3 run lines
    lines = summary.strip().splitlines()
    assert len(lines) == 4


def test_forecast_summary_contains_utc_label():
    after = _utc(2024, 1, 1, 0, 0)
    summary = forecast_summary("* * * * *", count=1, after=after)
    assert "UTC" in summary
