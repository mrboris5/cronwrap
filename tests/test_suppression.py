"""Tests for cronwrap.suppression and cronwrap.suppression_cli."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwrap.suppression import (
    is_suppressed,
    list_suppressions,
    load_suppressions,
    suppress_job,
    suppression_reason,
    unsuppress_job,
)
from cronwrap.suppression_cli import build_suppression_parser, suppression_main


@pytest.fixture
def sfile(tmp_path):
    return str(tmp_path / "suppressions.json")


# ── suppression module ────────────────────────────────────────────────────────

def test_load_suppressions_missing_file(sfile):
    assert load_suppressions(sfile) == {}


def test_load_suppressions_corrupt_file(sfile):
    Path(sfile).write_text("not json")
    assert load_suppressions(sfile) == {}


def test_suppress_job_creates_entry(sfile):
    entry = suppress_job(sfile, "backup", 3600)
    assert entry["job_id"] == "backup"
    assert "until" in entry
    assert "suppressed_at" in entry


def test_suppress_job_persists(sfile):
    suppress_job(sfile, "backup", 3600)
    data = load_suppressions(sfile)
    assert "backup" in data


def test_suppress_job_with_reason(sfile):
    entry = suppress_job(sfile, "sync", 60, reason="maintenance")
    assert entry["reason"] == "maintenance"


def test_is_suppressed_active(sfile):
    suppress_job(sfile, "job1", 3600)
    assert is_suppressed(sfile, "job1") is True


def test_is_suppressed_expired(sfile):
    suppress_job(sfile, "job1", -1)  # already expired
    assert is_suppressed(sfile, "job1") is False


def test_is_suppressed_unknown_job(sfile):
    assert is_suppressed(sfile, "ghost") is False


def test_unsuppress_job_removes_entry(sfile):
    suppress_job(sfile, "job2", 3600)
    removed = unsuppress_job(sfile, "job2")
    assert removed is True
    assert is_suppressed(sfile, "job2") is False


def test_unsuppress_job_nonexistent(sfile):
    assert unsuppress_job(sfile, "ghost") is False


def test_suppression_reason_active(sfile):
    suppress_job(sfile, "job3", 3600, reason="planned outage")
    reason = suppression_reason(sfile, "job3")
    assert reason is not None
    assert "planned outage" in reason


def test_suppression_reason_not_suppressed(sfile):
    assert suppression_reason(sfile, "job3") is None


def test_list_suppressions_returns_active(sfile):
    suppress_job(sfile, "a", 3600)
    suppress_job(sfile, "b", 7200)
    suppress_job(sfile, "c", -1)  # expired
    active = list_suppressions(sfile)
    ids = [e["job_id"] for e in active]
    assert "a" in ids
    assert "b" in ids
    assert "c" not in ids


# ── suppression CLI ───────────────────────────────────────────────────────────

def _run(argv):
    return suppression_main(argv)


def test_build_suppression_parser_returns_parser():
    p = build_suppression_parser()
    assert p is not None


def test_no_subcommand_returns_1(sfile):
    assert _run(["--file", sfile]) == 1


def test_add_exits_0(sfile):
    assert _run(["--file", sfile, "add", "myjob", "1h"]) == 0


def test_remove_exits_0(sfile, capsys):
    suppress_job(sfile, "myjob", 3600)
    assert _run(["--file", sfile, "remove", "myjob"]) == 0
    out = capsys.readouterr().out
    assert "removed" in out


def test_remove_nonexistent_exits_0(sfile, capsys):
    assert _run(["--file", sfile, "remove", "ghost"]) == 0
    out = capsys.readouterr().out
    assert "No active" in out


def test_check_suppressed(sfile, capsys):
    suppress_job(sfile, "myjob", 3600, reason="testing")
    _run(["--file", sfile, "check", "myjob"])
    out = capsys.readouterr().out
    assert "testing" in out


def test_check_not_suppressed(sfile, capsys):
    _run(["--file", sfile, "check", "myjob"])
    out = capsys.readouterr().out
    assert "not suppressed" in out


def test_list_empty(sfile, capsys):
    _run(["--file", sfile, "list"])
    out = capsys.readouterr().out
    assert "No active" in out


def test_list_shows_entries(sfile, capsys):
    suppress_job(sfile, "job_a", 3600)
    _run(["--file", sfile, "list"])
    out = capsys.readouterr().out
    assert "job_a" in out
