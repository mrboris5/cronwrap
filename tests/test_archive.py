"""Tests for cronwrap.archive and cronwrap.archive_cli."""
from __future__ import annotations

import gzip
import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from cronwrap.archive import (
    archive_entries,
    archive_summary,
    read_archive,
    write_archive,
)
from cronwrap.archive_cli import archive_main, build_archive_parser


def _iso(dt: datetime) -> str:
    return dt.isoformat()


_utcnow = datetime.now(timezone.utc)


@pytest.fixture
def arc_file(tmp_path):
    return str(tmp_path / "archive.jsonl.gz")


def _entry(days_ago: int) -> dict:
    ts = _utcnow - timedelta(days=days_ago)
    return {"timestamp": _iso(ts), "job_id": "job1", "status": "success"}


# --- archive_entries ---

def test_archive_entries_keeps_recent():
    entries = [_entry(1), _entry(5)]
    keep, old = archive_entries(entries, max_age_days=30)
    assert len(keep) == 2
    assert old == []


def test_archive_entries_removes_old():
    entries = [_entry(100), _entry(5)]
    keep, old = archive_entries(entries, max_age_days=30)
    assert len(keep) == 1
    assert len(old) == 1
    assert old[0] == entries[0]


def test_archive_entries_bad_timestamp_stays():
    entry = {"timestamp": "not-a-date", "job_id": "x"}
    keep, old = archive_entries([entry], max_age_days=1)
    assert entry in keep
    assert old == []


# --- write_archive / read_archive ---

def test_read_archive_missing_file(arc_file):
    assert read_archive(arc_file) == []


def test_write_and_read_roundtrip(arc_file):
    entries = [_entry(1), _entry(2)]
    written = write_archive(arc_file, entries)
    assert written == 2
    loaded = read_archive(arc_file)
    assert len(loaded) == 2
    assert loaded[0]["job_id"] == "job1"


def test_write_appends(arc_file):
    write_archive(arc_file, [_entry(1)])
    write_archive(arc_file, [_entry(2)])
    loaded = read_archive(arc_file)
    assert len(loaded) == 2


def test_write_empty_returns_zero(arc_file):
    assert write_archive(arc_file, []) == 0
    assert not os.path.exists(arc_file)


def test_read_archive_corrupt_lines(arc_file):
    with gzip.open(arc_file, "wt", encoding="utf-8") as fh:
        fh.write("not-json\n")
        fh.write(json.dumps({"ok": True}) + "\n")
    result = read_archive(arc_file)
    assert result == [{"ok": True}]


# --- archive_summary ---

def test_archive_summary_missing_file(arc_file):
    s = archive_summary(arc_file)
    assert s["entry_count"] == 0
    assert s["file_size_bytes"] == 0


def test_archive_summary_with_data(arc_file):
    write_archive(arc_file, [_entry(1), _entry(2)])
    s = archive_summary(arc_file)
    assert s["entry_count"] == 2
    assert s["file_size_bytes"] > 0


# --- CLI ---

def _run(args, arc_file):
    return archive_main(["--file", arc_file] + args)


def test_build_archive_parser_returns_parser():
    assert isinstance(build_archive_parser(), __import__("argparse").ArgumentParser)


def test_no_subcommand_returns_1(arc_file):
    assert _run([], arc_file) == 1


def test_show_exits_0(arc_file):
    assert _run(["show"], arc_file) == 0


def test_show_json_exits_0(arc_file):
    assert _run(["show", "--json"], arc_file) == 0


def test_read_exits_0(arc_file):
    assert _run(["read"], arc_file) == 0


def test_write_exits_0(arc_file):
    entry = json.dumps({"job_id": "j", "timestamp": _iso(_utcnow)})
    assert _run(["write", entry], arc_file) == 0


def test_write_invalid_json_returns_2(arc_file):
    assert _run(["write", "not-json"], arc_file) == 2
