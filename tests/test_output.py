"""Tests for cronwrap.output."""

from __future__ import annotations

import json
import os
import pytest

from cronwrap.output import (
    get_outputs,
    last_output,
    load_outputs,
    record_output,
    save_outputs,
)


@pytest.fixture()
def ofile(tmp_path):
    return str(tmp_path / "outputs.json")


def test_load_outputs_missing_file(ofile):
    assert load_outputs(ofile) == {}


def test_load_outputs_corrupt_file(ofile):
    with open(ofile, "w") as fh:
        fh.write("not json")
    assert load_outputs(ofile) == {}


def test_save_and_load_roundtrip(ofile):
    data = {"myjob": [{"timestamp": "t", "exit_code": 0, "stdout": "", "stderr": ""}]}
    save_outputs(ofile, data)
    assert load_outputs(ofile) == data


def test_record_output_creates_entry(ofile):
    entry = record_output(ofile, "backup", "ok", "", 0)
    assert entry["exit_code"] == 0
    assert entry["stdout"] == "ok"
    assert "timestamp" in entry


def test_record_output_appends(ofile):
    record_output(ofile, "backup", "first", "", 0)
    record_output(ofile, "backup", "second", "", 0)
    entries = get_outputs(ofile, "backup", limit=10)
    assert len(entries) == 2
    assert entries[0]["stdout"] == "first"
    assert entries[1]["stdout"] == "second"


def test_record_output_trims_to_max(ofile):
    for i in range(5):
        record_output(ofile, "job", str(i), "", 0, max_entries=3)
    entries = get_outputs(ofile, "job", limit=10)
    assert len(entries) == 3
    assert entries[-1]["stdout"] == "4"


def test_last_output_none_when_missing(ofile):
    assert last_output(ofile, "nonexistent") is None


def test_last_output_returns_most_recent(ofile):
    record_output(ofile, "job", "a", "", 0)
    record_output(ofile, "job", "b", "", 1)
    entry = last_output(ofile, "job")
    assert entry["stdout"] == "b"
    assert entry["exit_code"] == 1


def test_get_outputs_respects_limit(ofile):
    for i in range(10):
        record_output(ofile, "job", str(i), "", 0)
    entries = get_outputs(ofile, "job", limit=4)
    assert len(entries) == 4
    assert entries[-1]["stdout"] == "9"


def test_multiple_jobs_isolated(ofile):
    record_output(ofile, "job_a", "a-out", "", 0)
    record_output(ofile, "job_b", "b-out", "", 1)
    assert last_output(ofile, "job_a")["stdout"] == "a-out"
    assert last_output(ofile, "job_b")["exit_code"] == 1


def test_record_output_captures_stderr(ofile):
    entry = record_output(ofile, "job", "", "error occurred", 2)
    assert entry["stderr"] == "error occurred"
    assert entry["exit_code"] == 2
