"""Tests for cronwrap.replay."""
import json
import pytest
from cronwrap.replay import (
    load_replays,
    save_replays,
    record_replay,
    mark_replayed,
    pending_replays,
)


@pytest.fixture()
def rfile(tmp_path):
    return str(tmp_path / "replay.json")


def test_load_replays_missing_file(rfile):
    assert load_replays(rfile) == []


def test_load_replays_corrupt_file(rfile):
    with open(rfile, "w") as fh:
        fh.write("not json{{{")
    assert load_replays(rfile) == []


def test_save_and_load_roundtrip(rfile):
    entries = [{"job_id": "j1", "command": "echo hi", "exit_code": 1}]
    save_replays(rfile, entries)
    loaded = load_replays(rfile)
    assert len(loaded) == 1
    assert loaded[0]["job_id"] == "j1"


def test_save_trims_to_max_entries(rfile):
    entries = [{"n": i} for i in range(20)]
    save_replays(rfile, entries, max_entries=5)
    loaded = load_replays(rfile)
    assert len(loaded) == 5
    assert loaded[0]["n"] == 15


def test_record_replay_creates_entry(rfile):
    entry = record_replay(rfile, "job1", "echo fail", exit_code=1)
    assert entry["job_id"] == "job1"
    assert entry["command"] == "echo fail"
    assert entry["exit_code"] == 1
    assert entry["replayed"] is False
    assert entry["replay_at"] is None
    assert "recorded_at" in entry


def test_record_replay_persists(rfile):
    record_replay(rfile, "job1", "echo fail", exit_code=2)
    entries = load_replays(rfile)
    assert len(entries) == 1


def test_record_replay_captures_output(rfile):
    entry = record_replay(rfile, "j", "cmd", 1, stdout="out", stderr="err")
    assert entry["stdout"] == "out"
    assert entry["stderr"] == "err"


def test_mark_replayed_returns_true(rfile):
    record_replay(rfile, "job1", "echo fail", exit_code=1)
    result = mark_replayed(rfile, "job1", "echo fail")
    assert result is True


def test_mark_replayed_updates_entry(rfile):
    record_replay(rfile, "job1", "echo fail", exit_code=1)
    mark_replayed(rfile, "job1", "echo fail")
    entries = load_replays(rfile)
    assert entries[0]["replayed"] is True
    assert entries[0]["replay_at"] is not None


def test_mark_replayed_returns_false_when_not_found(rfile):
    result = mark_replayed(rfile, "ghost", "cmd")
    assert result is False


def test_pending_replays_returns_unplayed(rfile):
    record_replay(rfile, "j1", "cmd1", 1)
    record_replay(rfile, "j2", "cmd2", 1)
    mark_replayed(rfile, "j1", "cmd1")
    pending = pending_replays(rfile)
    assert len(pending) == 1
    assert pending[0]["job_id"] == "j2"


def test_pending_replays_filtered_by_job(rfile):
    record_replay(rfile, "j1", "cmd", 1)
    record_replay(rfile, "j2", "cmd", 1)
    pending = pending_replays(rfile, job_id="j1")
    assert len(pending) == 1
    assert pending[0]["job_id"] == "j1"
