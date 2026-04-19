"""Tests for cronwrap.audit."""

import json
import os
import pytest

from cronwrap.audit import append_audit, read_audit


@pytest.fixture
def audit_file(tmp_path):
    return str(tmp_path / "audit.jsonl")


def test_append_creates_file(audit_file):
    append_audit(audit_file, "job1", "echo hi", 0, 0.5)
    assert os.path.exists(audit_file)


def test_append_returns_entry(audit_file):
    entry = append_audit(audit_file, "job1", "echo hi", 0, 1.23, tags={"env": "prod"})
    assert entry["job_id"] == "job1"
    assert entry["command"] == "echo hi"
    assert entry["exit_code"] == 0
    assert entry["duration"] == 1.23
    assert entry["tags"] == {"env": "prod"}


def test_append_multiple_lines(audit_file):
    append_audit(audit_file, "job1", "cmd1", 0, 0.1)
    append_audit(audit_file, "job2", "cmd2", 1, 0.2)
    with open(audit_file) as fh:
        lines = [l for l in fh if l.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0])["job_id"] == "job1"
    assert json.loads(lines[1])["job_id"] == "job2"


def test_read_audit_missing_file(audit_file):
    assert read_audit(audit_file) == []


def test_read_audit_all(audit_file):
    append_audit(audit_file, "job1", "cmd", 0, 0.5)
    append_audit(audit_file, "job2", "cmd", 0, 0.6)
    entries = read_audit(audit_file)
    assert len(entries) == 2


def test_read_audit_filter_by_job_id(audit_file):
    append_audit(audit_file, "job1", "cmd", 0, 0.5)
    append_audit(audit_file, "job2", "cmd", 1, 0.6)
    append_audit(audit_file, "job1", "cmd", 0, 0.7)
    entries = read_audit(audit_file, job_id="job1")
    assert len(entries) == 2
    assert all(e["job_id"] == "job1" for e in entries)


def test_read_audit_skips_corrupt_lines(audit_file):
    with open(audit_file, "w") as fh:
        fh.write("not-json\n")
        fh.write(json.dumps({"job_id": "j", "command": "c", "exit_code": 0, "duration": 0.1, "tags": {}, "note": "", "ts": "x"}) + "\n")
    entries = read_audit(audit_file)
    assert len(entries) == 1


def test_entry_has_timestamp(audit_file):
    entry = append_audit(audit_file, "job1", "cmd", 0, 0.1)
    assert "ts" in entry
    assert entry["ts"].endswith("+00:00")


def test_note_field(audit_file):
    entry = append_audit(audit_file, "job1", "cmd", 0, 0.1, note="retry 2")
    assert entry["note"] == "retry 2"
    loaded = read_audit(audit_file)
    assert loaded[0]["note"] == "retry 2"
