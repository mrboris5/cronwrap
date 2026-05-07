"""Tests for cronwrap.trace and cronwrap.trace_cli."""
from __future__ import annotations

import json
import os
import pytest

from cronwrap.trace import (
    load_traces,
    save_traces,
    record_trace,
    last_trace,
    traces_for_job,
)
from cronwrap.trace_cli import build_trace_parser, trace_main


@pytest.fixture()
def tfile(tmp_path):
    return str(tmp_path / "traces.json")


def test_load_traces_missing_file(tfile):
    assert load_traces(tfile) == []


def test_load_traces_corrupt_file(tfile):
    with open(tfile, "w") as fh:
        fh.write("not json")
    assert load_traces(tfile) == []


def test_save_and_load_roundtrip(tfile):
    entries = [{"job_id": "j1", "exit_code": 0}]
    save_traces(tfile, entries)
    loaded = load_traces(tfile)
    assert loaded == entries


def test_save_trims_to_max_entries(tfile):
    entries = [{"job_id": f"j{i}"} for i in range(10)]
    save_traces(tfile, entries, max_entries=5)
    loaded = load_traces(tfile)
    assert len(loaded) == 5
    assert loaded[0]["job_id"] == "j5"


def test_record_trace_creates_entry(tfile):
    entry = record_trace(tfile, "backup", "rsync /src /dst", 0, 1.23)
    assert entry["job_id"] == "backup"
    assert entry["exit_code"] == 0
    assert entry["duration"] == 1.23
    assert "recorded_at" in entry


def test_record_trace_persists(tfile):
    record_trace(tfile, "backup", "rsync /src /dst", 0, 0.5)
    record_trace(tfile, "backup", "rsync /src /dst", 1, 0.8)
    traces = load_traces(tfile)
    assert len(traces) == 2


def test_last_trace_returns_most_recent(tfile):
    record_trace(tfile, "job-a", "cmd", 0, 1.0)
    record_trace(tfile, "job-a", "cmd", 1, 2.0)
    entry = last_trace(tfile, "job-a")
    assert entry["exit_code"] == 1


def test_last_trace_none_when_missing(tfile):
    assert last_trace(tfile, "ghost") is None


def test_traces_for_job_filters_correctly(tfile):
    record_trace(tfile, "job-a", "cmd", 0, 1.0)
    record_trace(tfile, "job-b", "cmd", 0, 1.0)
    record_trace(tfile, "job-a", "cmd", 0, 1.0)
    result = traces_for_job(tfile, "job-a")
    assert len(result) == 2
    assert all(r["job_id"] == "job-a" for r in result)


def test_record_trace_stores_tags(tfile):
    entry = record_trace(tfile, "j", "c", 0, 0.1, tags={"env": "prod"})
    assert entry["tags"] == {"env": "prod"}


# --- CLI tests ---

def _run(argv, tfile):
    return trace_main(["--file", tfile] + argv)


def test_build_trace_parser_returns_parser():
    p = build_trace_parser()
    assert p is not None


def test_no_subcommand_returns_1(tfile):
    assert _run([], tfile) == 1


def test_list_exits_0_empty(tfile, capsys):
    rc = _run(["list"], tfile)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No traces" in out


def test_list_shows_entries(tfile, capsys):
    record_trace(tfile, "j1", "echo hi", 0, 0.5)
    rc = _run(["list"], tfile)
    assert rc == 0
    out = capsys.readouterr().out
    assert "j1" in out


def test_list_filtered_by_job(tfile, capsys):
    record_trace(tfile, "j1", "echo", 0, 0.1)
    record_trace(tfile, "j2", "echo", 0, 0.1)
    rc = _run(["list", "--job", "j1"], tfile)
    assert rc == 0
    out = capsys.readouterr().out
    assert "j1" in out


def test_show_exits_0(tfile, capsys):
    record_trace(tfile, "myjob", "cmd", 0, 1.5)
    rc = _run(["show", "myjob"], tfile)
    assert rc == 0
    out = capsys.readouterr().out
    assert "myjob" in out


def test_show_missing_job_returns_1(tfile, capsys):
    rc = _run(["show", "nope"], tfile)
    assert rc == 1
