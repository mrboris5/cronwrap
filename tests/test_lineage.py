"""Tests for cronwrap.lineage and cronwrap.lineage_cli."""
from __future__ import annotations

import json
import pytest

from cronwrap.lineage import (
    find_children,
    get_lineage,
    lineage_summary,
    load_lineage,
    record_lineage,
    save_lineage,
)
from cronwrap.lineage_cli import build_lineage_parser, lineage_main


@pytest.fixture()
def lfile(tmp_path):
    return str(tmp_path / "lineage.json")


def test_load_lineage_missing_file(lfile):
    assert load_lineage(lfile) == {}


def test_load_lineage_corrupt_file(lfile):
    open(lfile, "w").write("not-json")
    assert load_lineage(lfile) == {}


def test_save_and_load_roundtrip(lfile):
    data = {"job-a": [{"run_id": "r1"}]}
    save_lineage(lfile, data)
    assert load_lineage(lfile) == data


def test_save_trims_to_max_entries(lfile):
    data = {"job-a": [{"run_id": str(i)} for i in range(10)]}
    save_lineage(lfile, data, max_entries=3)
    loaded = load_lineage(lfile)
    assert len(loaded["job-a"]) == 3
    assert loaded["job-a"][-1]["run_id"] == "9"


def test_record_lineage_creates_entry(lfile):
    entry = record_lineage(lfile, "job-x", "run-001")
    assert entry["run_id"] == "run-001"
    assert "parent_run_id" not in entry


def test_record_lineage_with_parent(lfile):
    entry = record_lineage(lfile, "job-x", "run-002", parent_run_id="run-001")
    assert entry["parent_run_id"] == "run-001"


def test_record_lineage_with_triggered_by(lfile):
    entry = record_lineage(lfile, "job-x", "run-003", triggered_by="scheduler")
    assert entry["triggered_by"] == "scheduler"


def test_record_lineage_persists(lfile):
    record_lineage(lfile, "job-x", "run-001")
    record_lineage(lfile, "job-x", "run-002")
    entries = get_lineage(lfile, "job-x")
    assert len(entries) == 2


def test_get_lineage_unknown_job(lfile):
    assert get_lineage(lfile, "no-such-job") == []


def test_find_children_returns_matching(lfile):
    record_lineage(lfile, "job-a", "r1")
    record_lineage(lfile, "job-b", "r2", parent_run_id="r1")
    record_lineage(lfile, "job-c", "r3", parent_run_id="r1")
    children = find_children(lfile, "r1")
    job_ids = {c["job_id"] for c in children}
    assert job_ids == {"job-b", "job-c"}


def test_find_children_no_match(lfile):
    record_lineage(lfile, "job-a", "r1")
    assert find_children(lfile, "nonexistent") == []


def test_lineage_summary(lfile):
    record_lineage(lfile, "job-a", "r1")
    record_lineage(lfile, "job-a", "r2", parent_run_id="r1")
    summary = lineage_summary(lfile, "job-a")
    assert "job=job-a" in summary
    assert "total_runs=2" in summary
    assert "child_runs=1" in summary
    assert "root_runs=1" in summary


# --- CLI tests ---

def _run(args):
    return lineage_main(args)


def test_build_lineage_parser_returns_parser():
    p = build_lineage_parser()
    assert p is not None


def test_no_subcommand_returns_1(lfile):
    assert _run(["--file", lfile]) == 1


def test_cli_record_exits_0(lfile, capsys):
    rc = _run(["--file", lfile, "record", "job-a", "run-001", "--parent", "run-000"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "run-001" in out


def test_cli_show_exits_0(lfile, capsys):
    record_lineage(lfile, "job-a", "run-001")
    rc = _run(["--file", lfile, "show", "job-a"])
    assert rc == 0


def test_cli_children_exits_0(lfile, capsys):
    record_lineage(lfile, "job-b", "r2", parent_run_id="r1")
    rc = _run(["--file", lfile, "children", "r1"])
    assert rc == 0
    assert "job-b" in capsys.readouterr().out


def test_cli_summary_exits_0(lfile, capsys):
    record_lineage(lfile, "job-a", "r1")
    rc = _run(["--file", lfile, "summary", "job-a"])
    assert rc == 0
    assert "job=job-a" in capsys.readouterr().out
