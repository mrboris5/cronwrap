"""Tests for cronwrap.retention."""
import pytest
from datetime import datetime, timezone, timedelta
from cronwrap.retention import _parse_days, prune_by_age, prune_by_count, apply_retention


def _iso(dt: datetime) -> str:
    return dt.isoformat()


now = datetime.now(timezone.utc)


def test_parse_days_valid():
    assert _parse_days("7d") == 7
    assert _parse_days("30d") == 30


def test_parse_days_invalid():
    with pytest.raises(ValueError):
        _parse_days("7")
    with pytest.raises(ValueError):
        _parse_days("7h")


def test_prune_by_age_keeps_recent():
    entries = [{"timestamp": _iso(now - timedelta(days=1))}]
    result = prune_by_age(entries, "7d")
    assert len(result) == 1


def test_prune_by_age_removes_old():
    entries = [{"timestamp": _iso(now - timedelta(days=10))}]
    result = prune_by_age(entries, "7d")
    assert result == []


def test_prune_by_age_mixed():
    entries = [
        {"timestamp": _iso(now - timedelta(days=2))},
        {"timestamp": _iso(now - timedelta(days=20))},
        {"timestamp": _iso(now - timedelta(days=1))},
    ]
    result = prune_by_age(entries, "7d")
    assert len(result) == 2


def test_prune_by_age_keeps_bad_timestamp():
    entries = [{"timestamp": "not-a-date"}]
    result = prune_by_age(entries, "7d")
    assert len(result) == 1


def test_prune_by_age_custom_key():
    entries = [{"ts": _iso(now - timedelta(days=1))}]
    result = prune_by_age(entries, "7d", key="ts")
    assert len(result) == 1


def test_prune_by_count_trims():
    entries = [{"id": i} for i in range(10)]
    result = prune_by_count(entries, 3)
    assert len(result) == 3
    assert result[0]["id"] == 7


def test_prune_by_count_no_trim():
    entries = [{"id": i} for i in range(3)]
    result = prune_by_count(entries, 10)
    assert len(result) == 3


def test_prune_by_count_invalid():
    with pytest.raises(ValueError):
        prune_by_count([], 0)


def test_apply_retention_both():
    entries = [
        {"timestamp": _iso(now - timedelta(days=20))},
        {"timestamp": _iso(now - timedelta(days=2))},
        {"timestamp": _iso(now - timedelta(days=1))},
    ]
    result = apply_retention(entries, max_age="7d", max_count=1)
    assert len(result) == 1


def test_apply_retention_none():
    entries = [{"timestamp": _iso(now)}]
    result = apply_retention(entries)
    assert len(result) == 1
