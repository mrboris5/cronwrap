"""Tests for cronwrap.mutex."""

import os
import pytest
from cronwrap.mutex import (
    load_mutex,
    save_mutex,
    acquire_slot,
    release_slot,
    slot_count,
)


@pytest.fixture
def mfile(tmp_path):
    return str(tmp_path / "mutex.json")


def test_load_mutex_missing_file(mfile):
    assert load_mutex(mfile) == {}


def test_load_mutex_corrupt_file(mfile):
    with open(mfile, "w") as f:
        f.write("not json")
    assert load_mutex(mfile) == {}


def test_save_and_load_roundtrip(mfile):
    data = {"job1": {"holders": [], "max": 2}}
    save_mutex(mfile, data)
    assert load_mutex(mfile) == data


def test_acquire_slot_first_time(mfile):
    result = acquire_slot(mfile, "job1", pid=os.getpid(), max_slots=2)
    assert result is True


def test_acquire_slot_respects_max(mfile):
    pid = os.getpid()
    acquire_slot(mfile, "job1", pid=pid, max_slots=1)
    # Inject a fake second holder with a live pid to simulate another process.
    state = load_mutex(mfile)
    state["job1"]["holders"].append({"pid": pid, "acquired_at": 0.0})
    save_mutex(mfile, state)
    result = acquire_slot(mfile, "job1", pid=pid, max_slots=1)
    assert result is False


def test_acquire_slot_prunes_dead_pids(mfile):
    dead_pid = 999999
    state = {"job1": {"holders": [{"pid": dead_pid, "acquired_at": 0.0}], "max": 1}}
    save_mutex(mfile, state)
    result = acquire_slot(mfile, "job1", pid=os.getpid(), max_slots=1)
    assert result is True


def test_release_slot_removes_pid(mfile):
    pid = os.getpid()
    acquire_slot(mfile, "job1", pid=pid, max_slots=2)
    removed = release_slot(mfile, "job1", pid=pid)
    assert removed is True


def test_release_slot_missing_job(mfile):
    assert release_slot(mfile, "nonexistent", pid=os.getpid()) is False


def test_release_slot_wrong_pid(mfile):
    acquire_slot(mfile, "job1", pid=os.getpid(), max_slots=2)
    removed = release_slot(mfile, "job1", pid=999998)
    assert removed is False


def test_slot_count_empty(mfile):
    assert slot_count(mfile, "job1") == 0


def test_slot_count_after_acquire(mfile):
    acquire_slot(mfile, "job1", pid=os.getpid(), max_slots=3)
    assert slot_count(mfile, "job1") == 1


def test_slot_count_after_release(mfile):
    pid = os.getpid()
    acquire_slot(mfile, "job1", pid=pid, max_slots=3)
    release_slot(mfile, "job1", pid=pid)
    assert slot_count(mfile, "job1") == 0
