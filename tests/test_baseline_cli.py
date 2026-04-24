"""Tests for cronwrap.baseline_cli."""

import pytest

from cronwrap.baseline_cli import baseline_main, build_baseline_parser


@pytest.fixture
def bf(tmp_path):
    return str(tmp_path / "baselines.json")


def _run(bf, *args):
    return baseline_main(["--file", bf, *args])


def test_build_baseline_parser_returns_parser():
    p = build_baseline_parser()
    assert p is not None


def test_no_subcommand_returns_1(bf):
    assert baseline_main(["--file", bf]) == 1


def test_set_exits_0(bf):
    assert _run(bf, "set", "myjob", "60") == 0


def test_set_invalid_seconds_exits_2(bf):
    assert _run(bf, "set", "myjob", "-1") == 2


def test_get_existing_exits_0(bf):
    _run(bf, "set", "myjob", "45")
    assert _run(bf, "get", "myjob") == 0


def test_get_missing_exits_1(bf):
    assert _run(bf, "get", "ghost") == 1


def test_remove_existing_exits_0(bf):
    _run(bf, "set", "myjob", "30")
    assert _run(bf, "remove", "myjob") == 0


def test_remove_missing_exits_1(bf):
    assert _run(bf, "remove", "nobody") == 1


def test_list_empty(bf, capsys):
    code = _run(bf, "list")
    assert code == 0
    out = capsys.readouterr().out
    assert "No baselines" in out


def test_list_shows_entries(bf, capsys):
    _run(bf, "set", "alpha", "10")
    _run(bf, "set", "beta", "20")
    _run(bf, "list")
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out
