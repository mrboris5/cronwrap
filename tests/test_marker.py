"""Tests for cronwrap.marker."""
from __future__ import annotations

import json
import pytest

from cronwrap.marker import (
    add_marker,
    clear_markers,
    get_markers,
    load_markers,
    remove_marker,
    save_markers,
)


@pytest.fixture()
def mfile(tmp_path):
    return str(tmp_path / "markers.json")


def test_load_markers_missing_file(mfile):
    assert load_markers(mfile) == {}


def test_load_markers_corrupt_file(mfile, tmp_path):
    (tmp_path / "markers.json").write_text("not json")
    assert load_markers(mfile) == {}


def test_save_and_load_roundtrip(mfile):
    data = {"job1": [{"job_id": "job1", "name": "start", "note": "", "timestamp": "t"}]}
    save_markers(mfile, data)
    assert load_markers(mfile) == data


def test_add_marker_creates_entry(mfile):
    entry = add_marker(mfile, "job1", "checkpoint")
    assert entry["job_id"] == "job1"
    assert entry["name"] == "checkpoint"
    assert "timestamp" in entry


def test_add_marker_with_note(mfile):
    entry = add_marker(mfile, "job1", "done", note="all good")
    assert entry["note"] == "all good"


def test_add_marker_persists(mfile):
    add_marker(mfile, "job1", "step1")
    markers = get_markers(mfile, "job1")
    assert len(markers) == 1
    assert markers[0]["name"] == "step1"


def test_get_markers_newest_first(mfile):
    add_marker(mfile, "job1", "first")
    add_marker(mfile, "job1", "second")
    markers = get_markers(mfile, "job1")
    assert markers[0]["name"] == "second"
    assert markers[1]["name"] == "first"


def test_get_markers_unknown_job(mfile):
    assert get_markers(mfile, "ghost") == []


def test_remove_marker_by_name(mfile):
    add_marker(mfile, "job1", "keep")
    add_marker(mfile, "job1", "drop")
    add_marker(mfile, "job1", "drop")
    removed = remove_marker(mfile, "job1", "drop")
    assert removed == 2
    remaining = get_markers(mfile, "job1")
    assert all(m["name"] == "keep" for m in remaining)


def test_remove_marker_returns_zero_if_not_found(mfile):
    add_marker(mfile, "job1", "keep")
    assert remove_marker(mfile, "job1", "ghost") == 0


def test_clear_markers_removes_all(mfile):
    add_marker(mfile, "job1", "a")
    add_marker(mfile, "job1", "b")
    clear_markers(mfile, "job1")
    assert get_markers(mfile, "job1") == []


def test_save_trims_to_max_entries(mfile):
    entries = [
        {"job_id": "j", "name": str(i), "note": "", "timestamp": "t"}
        for i in range(600)
    ]
    save_markers(mfile, {"j": entries})
    data = load_markers(mfile)
    assert len(data["j"]) == 500
