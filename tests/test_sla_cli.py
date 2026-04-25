"""Tests for cronwrap.sla_cli module."""

import pytest
from pathlib import Path
from cronwrap.sla import record_sla_run
from cronwrap.sla_cli import build_sla_parser, sla_main


@pytest.fixture
def sf(tmp_path):
    return str(tmp_path / "sla.json")


def _run(sf, *args):
    return sla_main(["--file", sf] + list(args))


def test_build_sla_parser_returns_parser():
    p = build_sla_parser()
    assert p is not None


def test_no_subcommand_returns_1(sf):
    assert _run(sf) == 1


def test_show_exits_0(sf):
    record_sla_run(sf, "job1", duration=1.0, success=True)
    assert _run(sf, "show", "job1") == 0


def test_show_unknown_job_exits_0(sf, capsys):
    # show still returns 0 (returns empty summary)
    assert _run(sf, "show", "ghost") == 0
    out = capsys.readouterr().out
    assert "ghost" in out


def test_list_exits_0_no_records(sf, capsys):
    assert _run(sf, "list") == 0
    out = capsys.readouterr().out
    assert "No SLA records" in out


def test_list_shows_jobs(sf, capsys):
    record_sla_run(sf, "job1", duration=1.0, success=True)
    record_sla_run(sf, "job2", duration=2.0, success=False)
    assert _run(sf, "list") == 0
    out = capsys.readouterr().out
    assert "job1" in out
    assert "job2" in out


def test_list_min_violations_filter(sf, capsys):
    record_sla_run(sf, "clean", duration=1.0, success=True)
    record_sla_run(sf, "broken", duration=1.0, success=False)
    assert _run(sf, "list", "--min-violations", "1") == 0
    out = capsys.readouterr().out
    assert "broken" in out
    assert "clean" not in out


def test_history_exits_0(sf):
    record_sla_run(sf, "job1", duration=1.5, success=True)
    assert _run(sf, "history", "job1") == 0


def test_history_unknown_job_returns_1(sf):
    assert _run(sf, "history", "ghost") == 1


def test_history_limit(sf, capsys):
    for _ in range(20):
        record_sla_run(sf, "job1", duration=1.0, success=True)
    assert _run(sf, "history", "job1", "--limit", "5") == 0
    out = capsys.readouterr().out
    lines = [l for l in out.strip().splitlines() if l]
    assert len(lines) == 5
