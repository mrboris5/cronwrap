"""Tests for cronwrap.note."""
import json
import pytest
from pathlib import Path

from cronwrap.note import (
    add_note,
    clear_notes,
    get_notes,
    load_notes,
    remove_note,
    save_notes,
)


@pytest.fixture
def nfile(tmp_path):
    return tmp_path / "notes.json"


def test_load_notes_missing_file(nfile):
    assert load_notes(nfile) == {}


def test_load_notes_corrupt_file(nfile):
    nfile.write_text("not json")
    assert load_notes(nfile) == {}


def test_save_and_load_roundtrip(nfile):
    data = {"job1": ["first note", "second note"]}
    save_notes(data, nfile)
    assert load_notes(nfile) == data


def test_add_note_creates_entry(nfile):
    result = add_note("job1", "hello world", path=nfile)
    assert result == ["hello world"]


def test_add_note_appends(nfile):
    add_note("job1", "first", path=nfile)
    result = add_note("job1", "second", path=nfile)
    assert result == ["first", "second"]


def test_add_note_trims_to_max(nfile):
    from cronwrap.note import _MAX_NOTES
    for i in range(_MAX_NOTES + 5):
        add_note("job1", f"note {i}", path=nfile)
    notes = get_notes("job1", path=nfile)
    assert len(notes) == _MAX_NOTES
    assert notes[-1] == f"note {_MAX_NOTES + 4}"


def test_get_notes_empty(nfile):
    assert get_notes("missing", path=nfile) == []


def test_remove_note_valid(nfile):
    add_note("job1", "a", path=nfile)
    add_note("job1", "b", path=nfile)
    removed = remove_note("job1", 0, path=nfile)
    assert removed == "a"
    assert get_notes("job1", path=nfile) == ["b"]


def test_remove_note_out_of_range(nfile):
    add_note("job1", "only", path=nfile)
    assert remove_note("job1", 5, path=nfile) is None


def test_remove_note_negative_index(nfile):
    add_note("job1", "only", path=nfile)
    assert remove_note("job1", -1, path=nfile) is None


def test_clear_notes_returns_count(nfile):
    add_note("job1", "x", path=nfile)
    add_note("job1", "y", path=nfile)
    count = clear_notes("job1", path=nfile)
    assert count == 2
    assert get_notes("job1", path=nfile) == []


def test_clear_notes_missing_job(nfile):
    assert clear_notes("ghost", path=nfile) == 0
