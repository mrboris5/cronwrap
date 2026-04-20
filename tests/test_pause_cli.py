"""Tests for cronwrap.pause_cli."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cronwrap.pause import pause_job
from cronwrap.pause_cli import build_pause_parser, pause_main


@pytest.fixture()
def pf(tmp_path):
    return str(tmp_path / "paused.json")


def _run(args):
    return pause_main(args)


def test_build_pause_parser_returns_parser():
    parser = build_pause_parser()
    assert parser is not None


def test_no_subcommand_returns_1(pf):
    assert _run(["--file", pf]) == 1


def test_pause_exits_0(pf):
    assert _run(["--file", pf, "pause", "myjob"]) == 0


def test_pause_with_expiry_exits_0(pf):
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    assert _run(["--file", pf, "pause", "myjob", "--expires", future]) == 0


def test_resume_paused_job_exits_0(pf):
    pause_job("myjob", path=pf)
    assert _run(["--file", pf, "resume", "myjob"]) == 0


def test_resume_not_paused_exits_1(pf):
    assert _run(["--file", pf, "resume", "ghost"]) == 1


def test_status_paused_job(pf, capsys):
    pause_job("statusjob", path=pf)
    code = _run(["--file", pf, "status", "statusjob"])
    assert code == 0
    out = capsys.readouterr().out
    assert "paused" in out


def test_status_active_job(pf, capsys):
    code = _run(["--file", pf, "status", "activejob"])
    assert code == 0
    out = capsys.readouterr().out
    assert "active" in out


def test_list_empty(pf, capsys):
    code = _run(["--file", pf, "list"])
    assert code == 0
    out = capsys.readouterr().out
    assert "No jobs" in out


def test_list_shows_paused_jobs(pf, capsys):
    pause_job("job_a", path=pf)
    pause_job("job_b", path=pf)
    code = _run(["--file", pf, "list"])
    assert code == 0
    out = capsys.readouterr().out
    assert "job_a" in out
    assert "job_b" in out
