"""Tests for cronwrap.healthcheck and cronwrap.healthcheck_cli."""

import os
import pytest

from cronwrap.healthcheck import (
    all_job_ids,
    is_healthy,
    last_ping,
    load_healthchecks,
    record_ping,
    save_healthchecks,
)
from cronwrap.healthcheck_cli import build_healthcheck_parser, healthcheck_main


@pytest.fixture
def hc_file(tmp_path):
    return str(tmp_path / "healthchecks.json")


def test_load_healthchecks_missing_file(hc_file):
    data = load_healthchecks(hc_file)
    assert data == {}


def test_load_healthchecks_corrupt_file(hc_file):
    with open(hc_file, "w") as f:
        f.write("not-json")
    data = load_healthchecks(hc_file)
    assert data == {}


def test_save_and_load_roundtrip(hc_file):
    payload = {"job1": [{"status": "ok"}]}
    save_healthchecks(hc_file, payload)
    loaded = load_healthchecks(hc_file)
    assert loaded == payload


def test_record_ping_creates_entry(hc_file):
    entry = record_ping(hc_file, "backup", status="ok", detail="all good")
    assert entry["job_id"] == "backup"
    assert entry["status"] == "ok"
    assert entry["detail"] == "all good"
    assert "timestamp" in entry


def test_record_ping_persists(hc_file):
    record_ping(hc_file, "backup", status="ok")
    data = load_healthchecks(hc_file)
    assert "backup" in data
    assert len(data["backup"]) == 1


def test_record_ping_accumulates(hc_file):
    record_ping(hc_file, "job1", status="ok")
    record_ping(hc_file, "job1", status="fail")
    data = load_healthchecks(hc_file)
    assert len(data["job1"]) == 2


def test_last_ping_returns_most_recent(hc_file):
    record_ping(hc_file, "job1", status="ok")
    record_ping(hc_file, "job1", status="fail", detail="oops")
    entry = last_ping(hc_file, "job1")
    assert entry["status"] == "fail"


def test_last_ping_missing_job(hc_file):
    assert last_ping(hc_file, "ghost") is None


def test_is_healthy_true(hc_file):
    record_ping(hc_file, "job1", status="ok")
    assert is_healthy(hc_file, "job1") is True


def test_is_healthy_false_on_fail(hc_file):
    record_ping(hc_file, "job1", status="fail")
    assert is_healthy(hc_file, "job1") is False


def test_is_healthy_false_when_missing(hc_file):
    assert is_healthy(hc_file, "ghost") is False


def test_all_job_ids(hc_file):
    record_ping(hc_file, "a")
    record_ping(hc_file, "b")
    ids = all_job_ids(hc_file)
    assert set(ids) == {"a", "b"}


# --- CLI tests ---

@pytest.fixture
def _run(hc_file):
    def run(argv):
        return healthcheck_main(["--file", hc_file] + argv)
    return run


def test_build_healthcheck_parser_returns_parser():
    p = build_healthcheck_parser()
    assert p is not None


def test_no_subcommand_returns_1(hc_file):
    assert healthcheck_main(["--file", hc_file]) == 1


def test_ping_exits_0(_run):
    assert _run(["ping", "myjob"]) == 0


def test_show_exits_0(_run):
    _run(["ping", "myjob", "--status", "ok"])
    assert _run(["show", "myjob"]) == 0


def test_show_missing_job_returns_1(_run):
    assert _run(["show", "ghost"]) == 1


def test_list_exits_0(_run, capsys):
    _run(["ping", "jobA"])
    code = _run(["list"])
    assert code == 0
    out = capsys.readouterr().out
    assert "jobA" in out


def test_status_all_ok(_run):
    _run(["ping", "j1", "--status", "ok"])
    assert _run(["status"]) == 0


def test_status_with_fail_returns_2(_run):
    _run(["ping", "j1", "--status", "fail"])
    assert _run(["status"]) == 2
