"""Tests for cronwrap.chain and cronwrap.chain_cli."""

import pytest
from cronwrap.chain import (
    load_chains,
    register_chain,
    get_chain,
    remove_chain,
    advance_chain,
    current_step,
)
from cronwrap.chain_cli import build_chain_parser, chain_main


@pytest.fixture()
def cfile(tmp_path):
    return str(tmp_path / "chains.json")


def _run(argv, cfile):
    return chain_main(argv, default_path=cfile)


# --- chain.py unit tests ---

def test_load_chains_missing_file(cfile):
    assert load_chains(cfile) == {}


def test_load_chains_corrupt_file(tmp_path):
    p = tmp_path / "chains.json"
    p.write_text("not json")
    assert load_chains(str(p)) == {}


def test_register_chain_creates_entry(cfile):
    entry = register_chain(cfile, "deploy", ["build", "test", "publish"])
    assert entry["chain_id"] == "deploy"
    assert entry["steps"] == ["build", "test", "publish"]
    assert entry["status"] == "pending"
    assert entry["current_index"] == 0


def test_register_chain_persists(cfile):
    register_chain(cfile, "deploy", ["a", "b"])
    chains = load_chains(cfile)
    assert "deploy" in chains


def test_register_chain_empty_steps_raises(cfile):
    with pytest.raises(ValueError):
        register_chain(cfile, "bad", [])


def test_get_chain_returns_entry(cfile):
    register_chain(cfile, "pipe", ["step1"])
    entry = get_chain(cfile, "pipe")
    assert entry is not None
    assert entry["chain_id"] == "pipe"


def test_get_chain_missing_returns_none(cfile):
    assert get_chain(cfile, "ghost") is None


def test_remove_chain_returns_true(cfile):
    register_chain(cfile, "tmp", ["x"])
    assert remove_chain(cfile, "tmp") is True
    assert get_chain(cfile, "tmp") is None


def test_remove_chain_missing_returns_false(cfile):
    assert remove_chain(cfile, "nope") is False


def test_advance_chain_moves_index(cfile):
    register_chain(cfile, "seq", ["a", "b", "c"])
    entry = advance_chain(cfile, "seq")
    assert entry["current_index"] == 1
    assert entry["status"] == "running"


def test_advance_chain_completes(cfile):
    register_chain(cfile, "seq", ["a"])
    entry = advance_chain(cfile, "seq")
    assert entry["status"] == "complete"


def test_advance_chain_missing_raises(cfile):
    with pytest.raises(KeyError):
        advance_chain(cfile, "ghost")


def test_current_step_returns_step(cfile):
    register_chain(cfile, "s", ["first", "second"])
    entry = get_chain(cfile, "s")
    assert current_step(entry) == "first"


def test_current_step_complete_returns_none(cfile):
    register_chain(cfile, "s", ["only"])
    entry = advance_chain(cfile, "s")
    assert current_step(entry) is None


# --- chain_cli.py tests ---

def test_build_chain_parser_returns_parser(cfile):
    p = build_chain_parser(cfile)
    assert p is not None


def test_no_subcommand_returns_1(cfile):
    assert _run([], cfile) == 1


def test_register_exits_0(cfile):
    assert _run(["--file", cfile, "register", "myjob", "s1", "s2"], cfile) == 0


def test_show_exits_0(cfile):
    _run(["--file", cfile, "register", "myjob", "s1"], cfile)
    assert _run(["--file", cfile, "show", "myjob"], cfile) == 0


def test_show_missing_returns_2(cfile):
    assert _run(["--file", cfile, "show", "ghost"], cfile) == 2


def test_list_exits_0(cfile):
    assert _run(["--file", cfile, "list"], cfile) == 0


def test_advance_exits_0(cfile):
    _run(["--file", cfile, "register", "ch", "s1", "s2"], cfile)
    assert _run(["--file", cfile, "advance", "ch"], cfile) == 0


def test_remove_exits_0(cfile):
    _run(["--file", cfile, "register", "ch", "s1"], cfile)
    assert _run(["--file", cfile, "remove", "ch"], cfile) == 0


def test_remove_missing_returns_2(cfile):
    assert _run(["--file", cfile, "remove", "ghost"], cfile) == 2
