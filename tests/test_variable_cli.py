"""Tests for cronwrap.variable_cli."""
from __future__ import annotations

import pytest

from cronwrap.variable_cli import build_variable_parser, variable_main


@pytest.fixture()
def vf(tmp_path):
    return str(tmp_path / "variables.json")


def _run(vf, *args):
    return variable_main(["--file", vf, *args])


def test_build_variable_parser_returns_parser():
    p = build_variable_parser()
    assert p is not None


def test_no_subcommand_returns_1(vf):
    assert variable_main(["--file", vf]) == 1


def test_set_exits_0(vf):
    assert _run(vf, "set", "job1", "retries", "3") == 0


def test_get_exits_0_after_set(vf):
    _run(vf, "set", "job1", "mode", "fast")
    assert _run(vf, "get", "job1", "mode") == 0


def test_get_missing_returns_1(vf):
    assert _run(vf, "get", "ghost", "key") == 1


def test_list_exits_0(vf):
    _run(vf, "set", "job1", "a", "1")
    assert _run(vf, "list", "job1") == 0


def test_list_empty_job_exits_0(vf):
    assert _run(vf, "list", "nobody") == 0


def test_remove_exits_0_after_set(vf):
    _run(vf, "set", "job1", "k", "v")
    assert _run(vf, "remove", "job1", "k") == 0


def test_remove_missing_returns_1(vf):
    assert _run(vf, "remove", "job1", "ghost") == 1


def test_clear_exits_0(vf):
    _run(vf, "set", "job1", "x", "10")
    assert _run(vf, "clear", "job1") == 0


def test_set_json_value(vf, capsys):
    _run(vf, "set", "job1", "count", "42")
    _run(vf, "get", "job1", "count")
    captured = capsys.readouterr()
    assert "42" in captured.out
