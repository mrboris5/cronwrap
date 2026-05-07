"""Tests for cronwrap.tombstone."""
import json
import pytest
from pathlib import Path

from cronwrap.tombstone import (
    load_tombstones,
    save_tombstones,
    bury_job,
    is_buried,
    get_tombstone,
    remove_tombstone,
    all_tombstones,
)


@pytest.fixture
def tfile(tmp_path) -> str:
    return str(tmp_path / "tombstones.json")


def test_load_tombstones_missing_file(tfile):
    result = load_tombstones(tfile)
    assert result == {}


def test_load_tombstones_corrupt_file(tfile):
    Path(tfile).parent.mkdir(parents=True, exist_ok=True)
    Path(tfile).write_text("not-json")
    result = load_tombstones(tfile)
    assert result == {}


def test_save_and_load_roundtrip(tfile):
    data = {"job-a": {"job_id": "job-a", "buried_at": "2024-01-01T00:00:00+00:00", "reason": "retired"}}
    save_tombstones(data, tfile)
    loaded = load_tombstones(tfile)
    assert loaded == data


def test_bury_job_creates_entry(tfile):
    entry = bury_job("my-job", reason="decommissioned", path=tfile)
    assert entry["job_id"] == "my-job"
    assert entry["reason"] == "decommissioned"
    assert "buried_at" in entry


def test_bury_job_persists(tfile):
    bury_job("job-x", path=tfile)
    records = load_tombstones(tfile)
    assert "job-x" in records


def test_bury_job_overwrites_existing(tfile):
    bury_job("job-y", reason="first", path=tfile)
    bury_job("job-y", reason="second", path=tfile)
    entry = get_tombstone("job-y", tfile)
    assert entry["reason"] == "second"


def test_is_buried_true(tfile):
    bury_job("buried-job", path=tfile)
    assert is_buried("buried-job", tfile) is True


def test_is_buried_false(tfile):
    assert is_buried("ghost-job", tfile) is False


def test_get_tombstone_returns_entry(tfile):
    bury_job("job-z", reason="test", path=tfile)
    entry = get_tombstone("job-z", tfile)
    assert entry is not None
    assert entry["job_id"] == "job-z"


def test_get_tombstone_missing_returns_none(tfile):
    assert get_tombstone("no-such-job", tfile) is None


def test_remove_tombstone_returns_true(tfile):
    bury_job("rm-job", path=tfile)
    result = remove_tombstone("rm-job", tfile)
    assert result is True
    assert not is_buried("rm-job", tfile)


def test_remove_tombstone_missing_returns_false(tfile):
    result = remove_tombstone("nonexistent", tfile)
    assert result is False


def test_all_tombstones_sorted_descending(tfile):
    bury_job("alpha", path=tfile)
    bury_job("beta", path=tfile)
    bury_job("gamma", path=tfile)
    entries = all_tombstones(tfile)
    buried_ats = [e["buried_at"] for e in entries]
    assert buried_ats == sorted(buried_ats, reverse=True)


def test_all_tombstones_empty(tfile):
    assert all_tombstones(tfile) == []
