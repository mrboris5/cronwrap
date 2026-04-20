"""Tests for cronwrap.heartbeat and cronwrap.heartbeat_cli."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta

import pytest

from cronwrap.heartbeat import (
    load_heartbeats,
    save_heartbeats,
    record_heartbeat,
    last_heartbeat,
    is_stale,
    stale_jobs,
)
from cronwrap.heartbeat_cli import build_heartbeat_parser, heartbeat_main


@pytest.fixture()
def hb_file(tmp_path):
    return str(tmp_path / "heartbeats.json")


# ── heartbeat module ────────────────────────────────────────────────────────

def test_load_heartbeats_missing_file(hb_file):
    assert load_heartbeats(hb_file) == {}


def test_load_heartbeats_corrupt_file(hb_file):
    with open(hb_file, "w") as fh:
        fh.write("not json{{")
    assert load_heartbeats(hb_file) == {}


def test_save_and_load_roundtrip(hb_file):
    records = {"job-a": {"job_id": "job-a", "last_seen": "2024-01-01T00:00:00+00:00", "meta": {}}}
    save_heartbeats(hb_file, records)
    loaded = load_heartbeats(hb_file)
    assert loaded == records


def test_record_heartbeat_creates_entry(hb_file):
    entry = record_heartbeat(hb_file, "my-job")
    assert entry["job_id"] == "my-job"
    assert "last_seen" in entry
    assert entry["meta"] == {}


def test_record_heartbeat_with_meta(hb_file):
    entry = record_heartbeat(hb_file, "my-job", {"host": "srv1"})
    assert entry["meta"] == {"host": "srv1"}


def test_record_heartbeat_overwrites(hb_file):
    record_heartbeat(hb_file, "job-x")
    record_heartbeat(hb_file, "job-x", {"v": "2"})
    records = load_heartbeats(hb_file)
    assert len(records) == 1
    assert records["job-x"]["meta"] == {"v": "2"}


def test_last_heartbeat_none_when_missing(hb_file):
    assert last_heartbeat(hb_file, "ghost") is None


def test_last_heartbeat_returns_entry(hb_file):
    record_heartbeat(hb_file, "j1")
    entry = last_heartbeat(hb_file, "j1")
    assert entry is not None
    assert entry["job_id"] == "j1"


def test_is_stale_no_record(hb_file):
    assert is_stale(hb_file, "unknown", 60) is True


def test_is_stale_fresh_record(hb_file):
    record_heartbeat(hb_file, "fresh-job")
    assert is_stale(hb_file, "fresh-job", 3600) is False


def test_is_stale_old_record(hb_file):
    old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    save_heartbeats(hb_file, {"old-job": {"job_id": "old-job", "last_seen": old_ts, "meta": {}}})
    assert is_stale(hb_file, "old-job", 3600) is True


def test_stale_jobs_returns_list(hb_file):
    old_ts = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    record_heartbeat(hb_file, "fresh")
    save_heartbeats(hb_file, {
        **load_heartbeats(hb_file),
        "old": {"job_id": "old", "last_seen": old_ts, "meta": {}},
    })
    stale = stale_jobs(hb_file, 3600)
    assert "old" in stale
    assert "fresh" not in stale


# ── heartbeat CLI ────────────────────────────────────────────────────────────

def _run(argv):
    return heartbeat_main(argv)


def test_build_heartbeat_parser_returns_parser():
    p = build_heartbeat_parser()
    assert p is not None


def test_no_subcommand_returns_1(hb_file):
    assert _run(["--file", hb_file]) == 1


def test_ping_exits_0(hb_file):
    assert _run(["--file", hb_file, "ping", "job-a"]) == 0


def test_ping_with_meta(hb_file):
    _run(["--file", hb_file, "ping", "job-b", "--meta", "host=srv1", "env=prod"])
    entry = last_heartbeat(hb_file, "job-b")
    assert entry["meta"]["host"] == "srv1"


def test_show_missing_job_returns_1(hb_file):
    assert _run(["--file", hb_file, "show", "ghost"]) == 1


def test_show_existing_job_returns_0(hb_file):
    record_heartbeat(hb_file, "known")
    assert _run(["--file", hb_file, "show", "known"]) == 0


def test_stale_exits_0(hb_file):
    assert _run(["--file", hb_file, "stale", "--max-age", "60"]) == 0


def test_list_exits_0(hb_file):
    assert _run(["--file", hb_file, "list"]) == 0
