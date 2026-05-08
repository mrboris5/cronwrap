"""Tests for cronwrap.token_cli"""

import json
import time
import pytest
from pathlib import Path

from cronwrap.token_cli import build_token_parser, token_main
from cronwrap.token import save_tokens


@pytest.fixture
def tf(tmp_path):
    return str(tmp_path / "tokens.json")


def _run(tf, *args):
    return token_main(["--file", tf] + list(args))


def test_build_token_parser_returns_parser():
    p = build_token_parser()
    assert p is not None


def test_no_subcommand_returns_1(tf):
    assert _run(tf) == 1


def test_show_exits_0(tf, capsys):
    rc = _run(tf, "show", "myjob")
    assert rc == 0
    out = capsys.readouterr().out
    assert "myjob" in out
    assert "tokens available" in out


def test_consume_exits_0(tf, capsys):
    rc = _run(tf, "consume", "myjob")
    assert rc == 0
    out = capsys.readouterr().out
    assert "consumed" in out


def test_consume_no_tokens_returns_2(tf, capsys):
    save_tokens(tf, {"myjob": {"tokens": 0.0, "last_refill": time.time()}})
    rc = _run(tf, "consume", "myjob", "--rate", "0.0")
    assert rc == 2


def test_reset_exits_0(tf, capsys):
    rc = _run(tf, "reset", "myjob")
    assert rc == 0
    out = capsys.readouterr().out
    assert "reset" in out


def test_list_empty(tf, capsys):
    rc = _run(tf, "list")
    assert rc == 0
    out = capsys.readouterr().out
    assert "No token entries" in out


def test_list_shows_entries(tf, capsys):
    save_tokens(tf, {"job_a": {"tokens": 3.5, "last_refill": time.time()}})
    rc = _run(tf, "list")
    assert rc == 0
    out = capsys.readouterr().out
    assert "job_a" in out
