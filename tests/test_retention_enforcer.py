"""Tests for cronwrap.retention_enforcer."""
from datetime import datetime, timedelta, timezone

import pytest

from cronwrap.retention_enforcer import (
    apply_retention_policy,
    enforcement_summary,
)
from cronwrap.retention_policy import set_retention_policy


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture()
def pfile(tmp_path):
    return str(tmp_path / "ret_policies.json")


def _make_records(ages_days: list[float]) -> list[dict]:
    """Build records with timestamps offset from now by given ages (newest first)."""
    now = _utcnow()
    records = []
    for age in sorted(ages_days):  # smallest age = newest
        ts = now - timedelta(days=age)
        records.append({"timestamp": _iso(ts), "data": f"age={age}"})
    return records


def test_no_policy_returns_all_records(pfile):
    records = _make_records([0, 1, 5, 10])
    result = apply_retention_policy(pfile, "job1", records)
    assert result == records


def test_max_count_limits_records(pfile):
    set_retention_policy(pfile, "job1", max_count=2)
    records = _make_records([0, 1, 2, 3])
    result = apply_retention_policy(pfile, "job1", records)
    assert len(result) == 2
    assert result == records[:2]


def test_max_age_days_removes_old(pfile):
    set_retention_policy(pfile, "job2", max_age_days=3)
    records = _make_records([0.5, 1, 5, 10])  # last two are older than 3 days
    result = apply_retention_policy(pfile, "job2", records)
    assert len(result) == 2
    for rec in result:
        age_str = rec["data"]
        age = float(age_str.split("=")[1])
        assert age <= 3


def test_max_count_and_max_age_combined(pfile):
    set_retention_policy(pfile, "job3", max_age_days=5, max_count=3)
    records = _make_records([0, 1, 2, 4, 7, 10])
    result = apply_retention_policy(pfile, "job3", records)
    assert len(result) <= 3
    for rec in result:
        age = float(rec["data"].split("=")[1])
        assert age <= 5


def test_max_count_zero_returns_empty(pfile):
    set_retention_policy(pfile, "job4", max_count=0)
    records = _make_records([0, 1])
    result = apply_retention_policy(pfile, "job4", records)
    assert result == []


def test_record_with_bad_timestamp_is_kept(pfile):
    set_retention_policy(pfile, "job5", max_age_days=1)
    records = [{"timestamp": "not-a-date", "data": "x"}]
    result = apply_retention_policy(pfile, "job5", records)
    assert len(result) == 1


def test_enforcement_summary_format(pfile):
    set_retention_policy(pfile, "job6", max_count=5, max_age_days=30)
    summary = enforcement_summary(pfile, "job6", 10, 5)
    assert "job6" in summary
    assert "pruned=5" in summary
    assert "max_count=5" in summary
    assert "max_age_days=30" in summary


def test_enforcement_summary_no_policy(pfile):
    summary = enforcement_summary(pfile, "unknown_job", 3, 3)
    assert "pruned=0" in summary
    assert "policy=(none)" in summary
