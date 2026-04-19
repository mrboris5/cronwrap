"""Tests for cronwrap.snapshot."""

import json
import os
import pytest

from cronwrap.snapshot import (
    load_snapshots,
    save_snapshots,
    record_snapshot,
    last_snapshot,
)


@pytest.fixture
def snap_file(tmp_path):
    return str(tmp_path / "snapshots.json")


def test_load_snapshots_missing_file(snap_file):
    assert load_snapshots(snap_file) == []


def test_load_snapshots_corrupt_file(snap_file):
    with open(snap_file, "w") as f:
        f.write("not json")
    assert load_snapshots(snap_file) == []


def test_save_and_load_roundtrip(snap_file):
    entries = [{"job_id": "j1", "exit_code": 0}]
    save_snapshots(snap_file, entries)
    loaded = load_snapshots(snap_file)
    assert loaded == entries


def test_save_trims_to_max_entries(snap_file):
    entries = [{"job_id": f"j{i}"} for i in range(15)]
    save_snapshots(snap_file, entries, max_entries=5)
    loaded = load_snapshots(snap_file)
    assert len(loaded) == 5
    assert loaded[-1]["job_id"] == "j14"


def test_record_snapshot_returns_entry(snap_file):
    entry = record_snapshot(snap_file, "myjob", "echo hi", "hi", "", 0)
    assert entry["job_id"] == "myjob"
    assert entry["command"] == "echo hi"
    assert entry["stdout"] == "hi"
    assert entry["exit_code"] == 0
    assert "timestamp" in entry


def test_record_snapshot_persists(snap_file):
    record_snapshot(snap_file, "j1", "cmd", "out", "", 0)
    record_snapshot(snap_file, "j1", "cmd", "out2", "", 1)
    loaded = load_snapshots(snap_file)
    assert len(loaded) == 2


def test_last_snapshot_returns_most_recent(snap_file):
    record_snapshot(snap_file, "j1", "cmd", "first", "", 0)
    record_snapshot(snap_file, "j1", "cmd", "second", "", 0)
    snap = last_snapshot(snap_file, "j1")
    assert snap["stdout"] == "second"


def test_last_snapshot_filters_by_job_id(snap_file):
    record_snapshot(snap_file, "j1", "cmd", "from_j1", "", 0)
    record_snapshot(snap_file, "j2", "cmd", "from_j2", "", 0)
    snap = last_snapshot(snap_file, "j1")
    assert snap["stdout"] == "from_j1"


def test_last_snapshot_missing_job_returns_none(snap_file):
    assert last_snapshot(snap_file, "nonexistent") is None
