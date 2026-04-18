"""Tests for cronwrap.history module."""
import json
import os
import pytest

from cronwrap.history import (
    load_history,
    save_history,
    record_run,
    last_runs,
    MAX_ENTRIES,
)


@pytest.fixture
def hist_file(tmp_path):
    return str(tmp_path / "history.json")


def test_load_history_missing_file(hist_file):
    assert load_history(hist_file) == []


def test_load_history_corrupt_file(hist_file):
    with open(hist_file, "w") as fh:
        fh.write("not json{{{")
    assert load_history(hist_file) == []


def test_save_and_load_roundtrip(hist_file):
    entries = [{"command": "echo hi", "returncode": 0}]
    save_history(entries, hist_file)
    loaded = load_history(hist_file)
    assert loaded == entries


def test_save_trims_to_max_entries(hist_file):
    entries = [{"i": i} for i in range(MAX_ENTRIES + 20)]
    save_history(entries, hist_file)
    loaded = load_history(hist_file)
    assert len(loaded) == MAX_ENTRIES
    assert loaded[-1]["i"] == MAX_ENTRIES + 19


def test_record_run_creates_entry(hist_file):
    entry = record_run("ls -la", 0, 0.123, stdout="file", stderr="", path=hist_file)
    assert entry["command"] == "ls -la"
    assert entry["returncode"] == 0
    assert entry["success"] is True
    assert entry["duration"] == 0.123
    assert "timestamp" in entry


def test_record_run_failure(hist_file):
    entry = record_run("false", 1, 0.05, path=hist_file)
    assert entry["success"] is False


def test_record_run_appends(hist_file):
    record_run("cmd1", 0, 0.1, path=hist_file)
    record_run("cmd2", 0, 0.2, path=hist_file)
    entries = load_history(hist_file)
    assert len(entries) == 2
    assert entries[0]["command"] == "cmd1"


def test_last_runs_returns_n(hist_file):
    for i in range(15):
        record_run(f"cmd{i}", 0, 0.01, path=hist_file)
    recent = last_runs(5, hist_file)
    assert len(recent) == 5
    assert recent[-1]["command"] == "cmd14"


def test_stdout_truncated(hist_file):
    long_out = "x" * 5000
    entry = record_run("echo", 0, 0.0, stdout=long_out, path=hist_file)
    assert len(entry["stdout"]) == 2000
