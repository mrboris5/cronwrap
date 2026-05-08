"""Tests for cronwrap.slot."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone, timedelta

import pytest

from cronwrap.slot import (
    _parse_seconds,
    load_slots,
    save_slots,
    record_slot_use,
    uses_in_window,
    is_slot_exceeded,
    slot_exceeded_reason,
    reset_slots,
)


@pytest.fixture
def sfile(tmp_path):
    return str(tmp_path / "slots.json")


def _iso(offset_seconds: float = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


# --- _parse_seconds ---

def test_parse_seconds_s():
    assert _parse_seconds("30s") == 30

def test_parse_seconds_m():
    assert _parse_seconds("5m") == 300

def test_parse_seconds_h():
    assert _parse_seconds("2h") == 7200

def test_parse_seconds_d():
    assert _parse_seconds("1d") == 86400

def test_parse_seconds_invalid():
    with pytest.raises(ValueError):
        _parse_seconds("10x")


# --- load / save ---

def test_load_slots_missing_file(sfile):
    assert load_slots(sfile) == {}

def test_load_slots_corrupt_file(sfile):
    with open(sfile, "w") as f:
        f.write("not-json")
    assert load_slots(sfile) == {}

def test_save_and_load_roundtrip(sfile):
    data = {"job1": {"uses": ["2024-01-01T00:00:00+00:00"]}}
    save_slots(sfile, data)
    assert load_slots(sfile) == data


# --- record_slot_use ---

def test_record_slot_use_creates_entry(sfile):
    entry = record_slot_use(sfile, "myjob")
    assert len(entry["uses"]) == 1

def test_record_slot_use_appends(sfile):
    record_slot_use(sfile, "myjob")
    entry = record_slot_use(sfile, "myjob")
    assert len(entry["uses"]) == 2


# --- uses_in_window ---

def test_uses_in_window_recent_included(sfile):
    record_slot_use(sfile, "j")
    result = uses_in_window(sfile, "j", "1h")
    assert len(result) == 1

def test_uses_in_window_old_excluded(sfile):
    old = _iso(-7200)  # 2 hours ago
    data = {"j": {"uses": [old]}}
    save_slots(sfile, data)
    result = uses_in_window(sfile, "j", "1h")
    assert result == []


# --- is_slot_exceeded ---

def test_is_slot_exceeded_false_when_under(sfile):
    record_slot_use(sfile, "j")
    assert not is_slot_exceeded(sfile, "j", 5, "1h")

def test_is_slot_exceeded_true_when_at_limit(sfile):
    for _ in range(3):
        record_slot_use(sfile, "j")
    assert is_slot_exceeded(sfile, "j", 3, "1h")


# --- slot_exceeded_reason ---

def test_slot_exceeded_reason_contains_job(sfile):
    record_slot_use(sfile, "j")
    reason = slot_exceeded_reason(sfile, "j", 5, "1h")
    assert "j" in reason
    assert "1/5" in reason


# --- reset_slots ---

def test_reset_slots_clears_uses(sfile):
    record_slot_use(sfile, "j")
    reset_slots(sfile, "j")
    data = load_slots(sfile)
    assert data["j"]["uses"] == []

def test_reset_slots_missing_job_no_error(sfile):
    reset_slots(sfile, "ghost")  # should not raise
