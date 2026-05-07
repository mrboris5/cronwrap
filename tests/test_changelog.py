"""Tests for cronwrap.changelog and cronwrap.changelog_cli."""

import json
import pytest

from cronwrap.changelog import (
    clear_changelog,
    get_changes,
    load_changelog,
    record_change,
    save_changelog,
)
from cronwrap.changelog_cli import build_changelog_parser, changelog_main


@pytest.fixture()
def cfile(tmp_path):
    return str(tmp_path / "changelog.json")


def _run(args):
    return changelog_main(args)


# --- changelog module ---

def test_load_changelog_missing_file(cfile):
    assert load_changelog(cfile) == []


def test_load_changelog_corrupt_file(cfile):
    open(cfile, "w").write("not json")
    assert load_changelog(cfile) == []


def test_save_and_load_roundtrip(cfile):
    entries = [{"job_id": "j1", "field": "schedule", "old_value": "*", "new_value": "0 * * * *"}]
    save_changelog(cfile, entries)
    loaded = load_changelog(cfile)
    assert loaded == entries


def test_save_trims_to_max_entries(cfile, monkeypatch):
    import cronwrap.changelog as cl
    monkeypatch.setattr(cl, "MAX_ENTRIES", 3)
    entries = [{"seq": i} for i in range(10)]
    save_changelog(cfile, entries)
    assert len(load_changelog(cfile)) == 3
    assert load_changelog(cfile)[0]["seq"] == 7


def test_record_change_creates_entry(cfile):
    entry = record_change(cfile, "job1", "retries", 1, 3)
    assert entry["job_id"] == "job1"
    assert entry["field"] == "retries"
    assert entry["old_value"] == 1
    assert entry["new_value"] == 3
    assert "timestamp" in entry
    assert "author" not in entry


def test_record_change_with_author(cfile):
    entry = record_change(cfile, "job1", "timeout", "30s", "60s", author="alice")
    assert entry["author"] == "alice"


def test_record_change_persists(cfile):
    record_change(cfile, "job1", "schedule", "old", "new")
    record_change(cfile, "job1", "retries", 1, 2)
    assert len(load_changelog(cfile)) == 2


def test_get_changes_filters_by_job(cfile):
    record_change(cfile, "job1", "f", "a", "b")
    record_change(cfile, "job2", "f", "x", "y")
    results = get_changes(cfile, "job1")
    assert len(results) == 1
    assert results[0]["job_id"] == "job1"


def test_get_changes_filters_by_field(cfile):
    record_change(cfile, "job1", "schedule", "a", "b")
    record_change(cfile, "job1", "retries", 1, 2)
    results = get_changes(cfile, "job1", field="retries")
    assert len(results) == 1
    assert results[0]["field"] == "retries"


def test_clear_changelog_removes_entries(cfile):
    record_change(cfile, "job1", "f", "a", "b")
    record_change(cfile, "job2", "f", "x", "y")
    removed = clear_changelog(cfile, "job1")
    assert removed == 1
    assert get_changes(cfile, "job1") == []
    assert len(get_changes(cfile, "job2")) == 1


# --- changelog_cli ---

def test_build_changelog_parser_returns_parser(cfile):
    p = build_changelog_parser()
    assert p is not None


def test_no_subcommand_returns_1(cfile):
    assert _run(["--file", cfile]) == 1


def test_record_exits_0(cfile):
    assert _run(["--file", cfile, "record", "job1", "timeout", "30s", "60s"]) == 0


def test_show_exits_0(cfile):
    record_change(cfile, "job1", "schedule", "old", "new")
    assert _run(["--file", cfile, "show", "job1"]) == 0


def test_clear_exits_0(cfile):
    record_change(cfile, "job1", "f", "a", "b")
    assert _run(["--file", cfile, "clear", "job1"]) == 0
