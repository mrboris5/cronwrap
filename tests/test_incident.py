"""Tests for cronwrap.incident."""
import json
import os
import pytest

from cronwrap.incident import (
    active_incidents,
    close_incident,
    incident_history,
    load_incidents,
    open_incident,
    save_incidents,
)


@pytest.fixture()
def ifile(tmp_path):
    return str(tmp_path / "incidents.json")


def test_load_incidents_missing_file(ifile):
    assert load_incidents(ifile) == []


def test_load_incidents_corrupt_file(ifile):
    with open(ifile, "w") as fh:
        fh.write("not json")
    assert load_incidents(ifile) == []


def test_save_and_load_roundtrip(ifile):
    entries = [{"job_id": "job1", "status": "open", "reason": "fail", "opened_at": "2024-01-01T00:00:00+00:00", "closed_at": None}]
    save_incidents(ifile, entries)
    loaded = load_incidents(ifile)
    assert len(loaded) == 1
    assert loaded[0]["job_id"] == "job1"


def test_save_trims_to_max_entries(ifile):
    entries = [{"job_id": f"j{i}", "status": "open"} for i in range(10)]
    save_incidents(ifile, entries, max_entries=5)
    loaded = load_incidents(ifile)
    assert len(loaded) == 5
    assert loaded[0]["job_id"] == "j5"


def test_open_incident_creates_entry(ifile):
    entry = open_incident(ifile, "backup", "disk full")
    assert entry["job_id"] == "backup"
    assert entry["status"] == "open"
    assert entry["reason"] == "disk full"
    assert entry["closed_at"] is None
    assert "opened_at" in entry


def test_open_incident_persists(ifile):
    open_incident(ifile, "job1", "timeout")
    loaded = load_incidents(ifile)
    assert len(loaded) == 1


def test_close_incident_updates_status(ifile):
    open_incident(ifile, "job1", "error")
    entry = close_incident(ifile, "job1", "fixed")
    assert entry is not None
    assert entry["status"] == "closed"
    assert entry["resolution"] == "fixed"
    assert entry["closed_at"] is not None


def test_close_incident_no_open_returns_none(ifile):
    result = close_incident(ifile, "nonexistent")
    assert result is None


def test_close_incident_closes_most_recent(ifile):
    open_incident(ifile, "job1", "first")
    open_incident(ifile, "job1", "second")
    close_incident(ifile, "job1")
    incidents = load_incidents(ifile)
    open_ones = [e for e in incidents if e["status"] == "open"]
    closed_ones = [e for e in incidents if e["status"] == "closed"]
    assert len(open_ones) == 1
    assert len(closed_ones) == 1
    assert closed_ones[0]["reason"] == "second"


def test_active_incidents_returns_open_only(ifile):
    open_incident(ifile, "job1", "err")
    open_incident(ifile, "job2", "err")
    close_incident(ifile, "job1")
    active = active_incidents(ifile)
    assert len(active) == 1
    assert active[0]["job_id"] == "job2"


def test_active_incidents_filter_by_job(ifile):
    open_incident(ifile, "job1", "err")
    open_incident(ifile, "job2", "err")
    active = active_incidents(ifile, "job1")
    assert all(e["job_id"] == "job1" for e in active)


def test_incident_history_returns_all_statuses(ifile):
    open_incident(ifile, "job1", "err1")
    open_incident(ifile, "job1", "err2")
    close_incident(ifile, "job1")
    hist = incident_history(ifile, "job1")
    assert len(hist) == 2


def test_incident_history_filters_by_job(ifile):
    open_incident(ifile, "job1", "err")
    open_incident(ifile, "job2", "err")
    hist = incident_history(ifile, "job1")
    assert all(e["job_id"] == "job1" for e in hist)
