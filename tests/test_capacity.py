"""Tests for cronwrap.capacity."""

import pytest

from cronwrap.capacity import (
    _parse_percent,
    load_capacity,
    record_capacity,
    is_over_capacity,
    capacity_reason,
)

_TS = "2024-06-01T12:00:00"


@pytest.fixture()
def cap_file(tmp_path):
    return str(tmp_path / "capacity.json")


# --- _parse_percent ---

def test_parse_percent_plain():
    assert _parse_percent("75") == 75.0


def test_parse_percent_with_symbol():
    assert _parse_percent("50%") == 50.0


def test_parse_percent_zero():
    assert _parse_percent("0") == 0.0


def test_parse_percent_hundred():
    assert _parse_percent("100%") == 100.0


def test_parse_percent_invalid():
    with pytest.raises(ValueError):
        _parse_percent("abc")


def test_parse_percent_out_of_range():
    with pytest.raises(ValueError):
        _parse_percent("101")


# --- load_capacity ---

def test_load_capacity_missing_file(cap_file):
    assert load_capacity(cap_file) == {}


def test_load_capacity_corrupt_file(cap_file):
    with open(cap_file, "w") as f:
        f.write("not json")
    assert load_capacity(cap_file) == {}


def test_load_capacity_wrong_type(cap_file):
    import json
    with open(cap_file, "w") as f:
        json.dump([1, 2, 3], f)
    assert load_capacity(cap_file) == {}


# --- record_capacity ---

def test_record_capacity_creates_entry(cap_file):
    entry = record_capacity(cap_file, "job1", 30.0, 45.0, _TS)
    assert entry["cpu_percent"] == 30.0
    assert entry["mem_percent"] == 45.0
    assert entry["timestamp"] == _TS


def test_record_capacity_persists(cap_file):
    record_capacity(cap_file, "job1", 10.0, 20.0, _TS)
    data = load_capacity(cap_file)
    assert len(data["job1"]) == 1


def test_record_capacity_trims_to_max(cap_file):
    for i in range(5):
        record_capacity(cap_file, "job1", float(i), float(i), _TS, max_entries=3)
    data = load_capacity(cap_file)
    assert len(data["job1"]) == 3


def test_record_capacity_multiple_jobs(cap_file):
    record_capacity(cap_file, "jobA", 10.0, 10.0, _TS)
    record_capacity(cap_file, "jobB", 20.0, 20.0, _TS)
    data = load_capacity(cap_file)
    assert "jobA" in data and "jobB" in data


# --- is_over_capacity ---

def test_is_over_capacity_false_no_records(cap_file):
    assert is_over_capacity(cap_file, "ghost", cpu_limit="80%") is False


def test_is_over_capacity_cpu_exceeded(cap_file):
    record_capacity(cap_file, "job1", 90.0, 10.0, _TS)
    assert is_over_capacity(cap_file, "job1", cpu_limit="80%") is True


def test_is_over_capacity_mem_exceeded(cap_file):
    record_capacity(cap_file, "job1", 10.0, 95.0, _TS)
    assert is_over_capacity(cap_file, "job1", mem_limit="90") is True


def test_is_over_capacity_within_limits(cap_file):
    record_capacity(cap_file, "job1", 50.0, 50.0, _TS)
    assert is_over_capacity(cap_file, "job1", cpu_limit="80", mem_limit="80") is False


# --- capacity_reason ---

def test_capacity_reason_empty_when_no_records(cap_file):
    assert capacity_reason(cap_file, "ghost", cpu_limit="80") == ""


def test_capacity_reason_cpu_message(cap_file):
    record_capacity(cap_file, "job1", 85.0, 10.0, _TS)
    reason = capacity_reason(cap_file, "job1", cpu_limit="80")
    assert "CPU" in reason and "85.0" in reason


def test_capacity_reason_mem_message(cap_file):
    record_capacity(cap_file, "job1", 10.0, 92.0, _TS)
    reason = capacity_reason(cap_file, "job1", mem_limit="90%")
    assert "MEM" in reason and "92.0" in reason


def test_capacity_reason_both_exceeded(cap_file):
    record_capacity(cap_file, "job1", 95.0, 95.0, _TS)
    reason = capacity_reason(cap_file, "job1", cpu_limit="80", mem_limit="80")
    assert "CPU" in reason and "MEM" in reason
