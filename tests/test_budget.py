"""Tests for cronwrap.budget module."""

import pytest
from pathlib import Path

from cronwrap.budget import (
    _parse_seconds,
    load_budgets,
    save_budgets,
    record_duration,
    is_over_budget,
    budget_reason,
    clear_budget,
)


@pytest.fixture
def bfile(tmp_path: Path) -> str:
    return str(tmp_path / "budgets.json")


# --- _parse_seconds ---

def test_parse_seconds_s():
    assert _parse_seconds("45s") == 45.0

def test_parse_seconds_m():
    assert _parse_seconds("2m") == 120.0

def test_parse_seconds_h():
    assert _parse_seconds("1h") == 3600.0

def test_parse_seconds_d():
    assert _parse_seconds("1d") == 86400.0

def test_parse_seconds_invalid():
    with pytest.raises(ValueError):
        _parse_seconds("10x")


# --- load / save ---

def test_load_budgets_missing_file(bfile):
    assert load_budgets(bfile) == {}

def test_load_budgets_corrupt_file(bfile):
    Path(bfile).write_text("not json")
    assert load_budgets(bfile) == {}

def test_save_and_load_roundtrip(bfile):
    data = {"job1": {"samples": [1.0, 2.0], "total": 3.0, "count": 2}}
    save_budgets(bfile, data)
    loaded = load_budgets(bfile)
    assert loaded["job1"]["count"] == 2
    assert loaded["job1"]["total"] == 3.0


# --- record_duration ---

def test_record_duration_creates_entry(bfile):
    entry = record_duration(bfile, "myjob", 10.0)
    assert entry["count"] == 1
    assert entry["total"] == 10.0
    assert entry["samples"] == [10.0]

def test_record_duration_accumulates(bfile):
    record_duration(bfile, "myjob", 10.0)
    entry = record_duration(bfile, "myjob", 20.0)
    assert entry["count"] == 2
    assert entry["total"] == 30.0

def test_record_duration_trims_samples(bfile):
    for i in range(5):
        record_duration(bfile, "myjob", float(i), max_entries=3)
    data = load_budgets(bfile)
    assert len(data["myjob"]["samples"]) == 3


# --- is_over_budget ---

def test_is_over_budget_false_no_data(bfile):
    assert is_over_budget(bfile, "ghost", "10s") is False

def test_is_over_budget_false_within(bfile):
    record_duration(bfile, "j", 5.0)
    assert is_over_budget(bfile, "j", "10s") is False

def test_is_over_budget_true_exceeded(bfile):
    record_duration(bfile, "j", 20.0)
    assert is_over_budget(bfile, "j", "10s") is True


# --- budget_reason ---

def test_budget_reason_none_when_ok(bfile):
    record_duration(bfile, "j", 5.0)
    assert budget_reason(bfile, "j", "10s") is None

def test_budget_reason_message_when_over(bfile):
    record_duration(bfile, "j", 30.0)
    reason = budget_reason(bfile, "j", "10s")
    assert reason is not None
    assert "j" in reason
    assert "30.0s" in reason

def test_budget_reason_none_no_data(bfile):
    assert budget_reason(bfile, "unknown", "5s") is None


# --- clear_budget ---

def test_clear_budget_existing(bfile):
    record_duration(bfile, "j", 5.0)
    assert clear_budget(bfile, "j") is True
    assert load_budgets(bfile).get("j") is None

def test_clear_budget_nonexistent(bfile):
    assert clear_budget(bfile, "ghost") is False
