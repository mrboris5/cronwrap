"""Tests for cronwrap.trigger."""

import json
import os
import pytest

from cronwrap.trigger import (
    acknowledge_trigger,
    last_trigger,
    load_triggers,
    pending_triggers,
    record_trigger,
    save_triggers,
)


@pytest.fixture
def tfile(tmp_path):
    return str(tmp_path / "triggers.json")


def test_load_triggers_missing_file(tfile):
    assert load_triggers(tfile) == []


def test_load_triggers_corrupt_file(tfile):
    with open(tfile, "w") as fh:
        fh.write("not json")
    assert load_triggers(tfile) == []


def test_save_and_load_roundtrip(tfile):
    entries = [{"job_id": "j1", "trigger_type": "manual", "acknowledged": False}]
    save_triggers(tfile, entries)
    loaded = load_triggers(tfile)
    assert len(loaded) == 1
    assert loaded[0]["job_id"] == "j1"


def test_save_trims_to_max_entries(tfile):
    entries = [{"job_id": f"j{i}"} for i in range(10)]
    save_triggers(tfile, entries, max_entries=5)
    loaded = load_triggers(tfile)
    assert len(loaded) == 5
    assert loaded[0]["job_id"] == "j5"


def test_record_trigger_creates_entry(tfile):
    entry = record_trigger(tfile, "backup", "manual", source="cli", reason="test")
    assert entry["job_id"] == "backup"
    assert entry["trigger_type"] == "manual"
    assert entry["source"] == "cli"
    assert entry["reason"] == "test"
    assert "triggered_at" in entry
    assert entry["acknowledged"] is False


def test_record_trigger_persists(tfile):
    record_trigger(tfile, "job1", "event")
    record_trigger(tfile, "job2", "manual")
    entries = load_triggers(tfile)
    assert len(entries) == 2


def test_acknowledge_trigger_marks_latest(tfile):
    record_trigger(tfile, "job1", "manual")
    ok = acknowledge_trigger(tfile, "job1")
    assert ok is True
    entries = load_triggers(tfile)
    assert entries[-1]["acknowledged"] is True


def test_acknowledge_trigger_no_match_returns_false(tfile):
    ok = acknowledge_trigger(tfile, "nonexistent")
    assert ok is False


def test_acknowledge_trigger_already_acked_returns_false(tfile):
    record_trigger(tfile, "job1", "manual")
    acknowledge_trigger(tfile, "job1")
    ok = acknowledge_trigger(tfile, "job1")
    assert ok is False


def test_pending_triggers_returns_unacked(tfile):
    record_trigger(tfile, "job1", "manual")
    record_trigger(tfile, "job2", "event")
    acknowledge_trigger(tfile, "job1")
    pending = pending_triggers(tfile)
    assert len(pending) == 1
    assert pending[0]["job_id"] == "job2"


def test_pending_triggers_filtered_by_job(tfile):
    record_trigger(tfile, "job1", "manual")
    record_trigger(tfile, "job2", "event")
    pending = pending_triggers(tfile, job_id="job1")
    assert len(pending) == 1
    assert pending[0]["job_id"] == "job1"


def test_last_trigger_returns_most_recent(tfile):
    record_trigger(tfile, "job1", "manual", reason="first")
    record_trigger(tfile, "job1", "event", reason="second")
    entry = last_trigger(tfile, "job1")
    assert entry["reason"] == "second"


def test_last_trigger_no_entry_returns_none(tfile):
    assert last_trigger(tfile, "ghost") is None
