"""Tests for cronwrap.status and cronwrap.status_cli."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwrap.status import (
    all_statuses,
    compute_status,
    get_status,
    load_status,
    save_status,
    update_status,
)
from cronwrap.status_cli import build_status_parser, status_main


@pytest.fixture()
def sf(tmp_path):
    return tmp_path / "status.json"


def _runs(*exit_codes):
    return [{"exit_code": c, "timestamp": f"2024-01-01T00:0{i}:00"} for i, c in enumerate(exit_codes)]


def test_load_status_missing_file(sf):
    assert load_status(sf) == {}


def test_load_status_corrupt_file(sf):
    sf.write_text("not json")
    assert load_status(sf) == {}


def test_save_and_load_roundtrip(sf):
    data = {"job1": {"state": "ok"}}
    save_status(data, sf)
    assert load_status(sf) == data


def test_compute_status_no_runs():
    s = compute_status("j", [])
    assert s["state"] == "unknown"
    assert s["consecutive_failures"] == 0
    assert s["last_run"] is None


def test_compute_status_all_ok():
    s = compute_status("j", _runs(0, 0, 0))
    assert s["state"] == "ok"
    assert s["consecutive_failures"] == 0


def test_compute_status_one_failure():
    s = compute_status("j", _runs(1, 0, 0))
    assert s["state"] == "degraded"
    assert s["consecutive_failures"] == 1


def test_compute_status_three_failures():
    s = compute_status("j", _runs(1, 1, 1, 0))
    assert s["state"] == "failing"
    assert s["consecutive_failures"] == 3


def test_update_status_persists(sf):
    entry = update_status("myjob", _runs(0, 0), sf)
    assert entry["state"] == "ok"
    assert get_status("myjob", sf)["state"] == "ok"


def test_get_status_missing_job(sf):
    assert get_status("nope", sf) is None


def test_all_statuses_returns_list(sf):
    update_status("a", _runs(0), sf)
    update_status("b", _runs(1, 1, 1), sf)
    statuses = all_statuses(sf)
    assert len(statuses) == 2
    states = {s["job_id"]: s["state"] for s in statuses}
    assert states["a"] == "ok"
    assert states["b"] == "failing"


def _run(argv, sf):
    return status_main(["--file", str(sf)] + argv)


def test_build_status_parser_returns_parser():
    assert build_status_parser() is not None


def test_no_subcommand_returns_1(sf):
    assert _run([], sf) == 1


def test_list_exits_0(sf):
    update_status("job1", _runs(0), sf)
    assert _run(["list"], sf) == 0


def test_list_empty(sf):
    assert _run(["list"], sf) == 0


def test_list_filter_by_state(sf, capsys):
    update_status("good", _runs(0), sf)
    update_status("bad", _runs(1, 1, 1), sf)
    _run(["list", "--state", "ok"], sf)
    out = capsys.readouterr().out
    assert "good" in out
    assert "bad" not in out


def test_show_exits_0(sf):
    update_status("job1", _runs(0), sf)
    assert _run(["show", "job1"], sf) == 0


def test_show_missing_returns_1(sf):
    assert _run(["show", "ghost"], sf) == 1
