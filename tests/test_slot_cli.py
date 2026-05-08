"""Tests for cronwrap.slot_cli."""

from __future__ import annotations

import pytest

from cronwrap.slot_cli import build_slot_parser, slot_main
from cronwrap.slot import record_slot_use


@pytest.fixture
def sf(tmp_path):
    return str(tmp_path / "slots.json")


def _run(argv):
    return slot_main(argv)


def test_build_slot_parser_returns_parser():
    p = build_slot_parser()
    assert p is not None


def test_no_subcommand_returns_1(sf):
    assert _run(["--file", sf]) == 1 or _run([]) == 1


def test_record_exits_0(sf):
    assert _run(["record", "myjob", "--file", sf]) == 0


def test_show_exits_0(sf):
    record_slot_use(sf, "myjob")
    assert _run(["show", "myjob", "--window", "1h", "--file", sf]) == 0


def test_check_exits_0_when_under(sf):
    record_slot_use(sf, "myjob")
    assert _run(["check", "myjob", "--max", "5", "--window", "1h", "--file", sf]) == 0


def test_check_exits_1_when_exceeded(sf):
    for _ in range(3):
        record_slot_use(sf, "myjob")
    assert _run(["check", "myjob", "--max", "3", "--window", "1h", "--file", sf]) == 1


def test_reset_exits_0(sf):
    record_slot_use(sf, "myjob")
    assert _run(["reset", "myjob", "--file", sf]) == 0


def test_reset_clears_uses(sf):
    from cronwrap.slot import uses_in_window
    record_slot_use(sf, "myjob")
    _run(["reset", "myjob", "--file", sf])
    assert uses_in_window(sf, "myjob", "1h") == []
