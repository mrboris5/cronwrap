"""Tests for cronwrap.trigger_cli."""

import pytest

from cronwrap.trigger import record_trigger
from cronwrap.trigger_cli import build_trigger_parser, trigger_main


@pytest.fixture
def tf(tmp_path):
    return str(tmp_path / "triggers.json")


def _run(tf, *args):
    return trigger_main(["--file", tf, *args])


def test_build_trigger_parser_returns_parser():
    parser = build_trigger_parser()
    assert parser is not None


def test_no_subcommand_returns_1(tf):
    assert trigger_main(["--file", tf]) == 1


def test_fire_exits_0(tf):
    assert _run(tf, "fire", "myjob") == 0


def test_fire_records_entry(tf):
    _run(tf, "fire", "myjob", "--type", "event", "--source", "webhook", "--reason", "deploy")
    from cronwrap.trigger import load_triggers
    entries = load_triggers(tf)
    assert len(entries) == 1
    assert entries[0]["trigger_type"] == "event"
    assert entries[0]["source"] == "webhook"


def test_ack_exits_0(tf):
    record_trigger(tf, "myjob", "manual")
    assert _run(tf, "ack", "myjob") == 0


def test_ack_no_pending_returns_1(tf):
    assert _run(tf, "ack", "ghost") == 1


def test_pending_exits_0_empty(tf, capsys):
    rc = _run(tf, "pending")
    assert rc == 0
    out = capsys.readouterr().out
    assert "No pending" in out


def test_pending_shows_unacked(tf, capsys):
    record_trigger(tf, "job1", "manual")
    _run(tf, "pending")
    out = capsys.readouterr().out
    assert "job1" in out


def test_last_exits_0(tf, capsys):
    record_trigger(tf, "job1", "manual", reason="hello")
    rc = _run(tf, "last", "job1")
    assert rc == 0
    out = capsys.readouterr().out
    assert "job1" in out


def test_last_missing_returns_1(tf):
    assert _run(tf, "last", "ghost") == 1
