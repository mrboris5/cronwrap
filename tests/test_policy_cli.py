"""Tests for cronwrap.policy_cli."""

import json
from pathlib import Path

import pytest

from cronwrap.policy_cli import build_policy_parser, policy_main


@pytest.fixture()
def pf(tmp_path: Path) -> Path:
    return tmp_path / "policies.json"


def _run(args: list[str], pf: Path) -> int:
    return policy_main(["--file", str(pf)] + args)


def test_build_policy_parser_returns_parser():
    p = build_policy_parser()
    assert p is not None


def test_no_subcommand_returns_1(pf):
    assert _run([], pf) == 1


def test_set_exits_0(pf):
    assert _run(["set", "nightly", '{"retries": 3}'], pf) == 0
    assert pf.exists()


def test_set_invalid_json_returns_2(pf):
    assert _run(["set", "bad", "not-json"], pf) == 2


def test_list_empty(pf, capsys):
    assert _run(["list"], pf) == 0
    out = capsys.readouterr().out
    assert "no policies" in out


def test_list_shows_names(pf, capsys):
    _run(["set", "alpha", '{"x":1}'], pf)
    _run(["set", "beta", '{"x":2}'], pf)
    assert _run(["list"], pf) == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_get_existing(pf, capsys):
    _run(["set", "p", '{"retries": 2}'], pf)
    assert _run(["get", "p"], pf) == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["retries"] == 2


def test_get_missing_returns_1(pf):
    assert _run(["get", "ghost"], pf) == 1


def test_remove_existing_exits_0(pf):
    _run(["set", "tmp", '{"x":1}'], pf)
    assert _run(["remove", "tmp"], pf) == 0


def test_remove_missing_returns_1(pf):
    assert _run(["remove", "ghost"], pf) == 1


def test_apply_exits_0_and_merges(pf, capsys):
    _run(["set", "base", '{"retries": 5, "timeout": "1h"}'], pf)
    assert _run(["apply", "base", '{"alert": true}'], pf) == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["retries"] == 5
    assert data["alert"] is True


def test_apply_missing_policy_returns_1(pf):
    assert _run(["apply", "ghost", '{"x":1}'], pf) == 1


def test_apply_invalid_config_json_returns_2(pf):
    _run(["set", "p", '{"x":1}'], pf)
    assert _run(["apply", "p", "bad-json"], pf) == 2
