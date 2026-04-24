"""Tests for cronwrap.runbook_cli."""

import pytest

from cronwrap.runbook_cli import build_runbook_parser, runbook_main
from cronwrap.runbook import set_runbook


@pytest.fixture()
def rf(tmp_path):
    return str(tmp_path / "runbooks.json")


def _run(rf, *args):
    return runbook_main(["--file", rf, *args])


def test_build_runbook_parser_returns_parser():
    p = build_runbook_parser()
    assert p is not None


def test_no_subcommand_returns_1(rf):
    assert _run(rf) == 1


def test_set_exits_0(rf):
    assert _run(rf, "set", "myjob", "--url", "http://wiki/myjob") == 0


def test_set_and_get_exits_0(rf):
    _run(rf, "set", "myjob", "--owner", "alice")
    assert _run(rf, "get", "myjob") == 0


def test_get_missing_returns_1(rf):
    assert _run(rf, "get", "ghost") == 1


def test_remove_existing_exits_0(rf):
    _run(rf, "set", "myjob", "--url", "http://x")
    assert _run(rf, "remove", "myjob") == 0


def test_remove_nonexistent_returns_1(rf):
    assert _run(rf, "remove", "ghost") == 1


def test_list_empty(rf, capsys):
    _run(rf, "list")
    out = capsys.readouterr().out
    assert "No runbook" in out


def test_list_shows_ids(rf, capsys):
    _run(rf, "set", "job_a", "--url", "http://a")
    _run(rf, "set", "job_b", "--notes", "hello")
    _run(rf, "list")
    out = capsys.readouterr().out
    assert "job_a" in out
    assert "job_b" in out


def test_set_all_fields_exits_0(rf):
    rc = _run(
        rf, "set", "full_job",
        "--url", "http://wiki",
        "--notes", "important",
        "--owner", "bob",
        "--escalation-contact", "oncall@example.com",
    )
    assert rc == 0
