"""Tests for cronwrap.incident_cli."""
import os
import pytest

from cronwrap.incident_cli import build_incident_parser, incident_main


@pytest.fixture()
def ifile(tmp_path):
    return str(tmp_path / "incidents.json")


def _run(ifile, *args):
    return incident_main(["--file", ifile, *args])


def test_build_incident_parser_returns_parser():
    parser = build_incident_parser()
    assert parser is not None


def test_no_subcommand_returns_1(ifile):
    assert incident_main(["--file", ifile]) == 1


def test_open_exits_0(ifile):
    assert _run(ifile, "open", "backup", "disk full") == 0


def test_open_creates_incident(ifile):
    _run(ifile, "open", "job1", "timeout")
    from cronwrap.incident import load_incidents
    incidents = load_incidents(ifile)
    assert len(incidents) == 1
    assert incidents[0]["job_id"] == "job1"


def test_close_exits_0(ifile):
    _run(ifile, "open", "job1", "err")
    assert _run(ifile, "close", "job1", "--resolution", "fixed") == 0


def test_close_no_open_returns_1(ifile):
    assert _run(ifile, "close", "ghost-job") == 1


def test_list_exits_0(ifile):
    assert _run(ifile, "list") == 0


def test_list_with_job_filter(ifile):
    _run(ifile, "open", "job1", "err")
    assert _run(ifile, "list", "--job", "job1") == 0


def test_history_exits_0(ifile):
    _run(ifile, "open", "job1", "err")
    assert _run(ifile, "history", "job1") == 0


def test_history_no_entries(ifile, capsys):
    _run(ifile, "history", "unknown-job")
    captured = capsys.readouterr()
    assert "No incidents" in captured.out
