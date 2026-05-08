"""Tests for cronwrap.alias and cronwrap.alias_cli."""

import pytest
from pathlib import Path

from cronwrap.alias import (
    all_aliases,
    get_alias,
    load_aliases,
    remove_alias,
    resolve,
    set_alias,
)
from cronwrap.alias_cli import alias_main, build_alias_parser


@pytest.fixture()
def afile(tmp_path) -> Path:
    return tmp_path / "aliases.json"


def _run(argv, afile):
    return alias_main(["--file", str(afile)] + argv)


# --- module tests ---

def test_load_aliases_missing_file(afile):
    assert load_aliases(afile) == {}


def test_load_aliases_corrupt_file(afile):
    afile.write_text("not json")
    assert load_aliases(afile) == {}


def test_save_and_load_roundtrip(afile):
    set_alias("daily", "job:daily-report", afile)
    assert load_aliases(afile) == {"daily": "job:daily-report"}


def test_set_alias_creates_entry(afile):
    result = set_alias("nightly", "job:nightly-backup", afile)
    assert result["nightly"] == "job:nightly-backup"


def test_set_alias_overwrites_existing(afile):
    set_alias("x", "job:old", afile)
    set_alias("x", "job:new", afile)
    assert get_alias("x", afile) == "job:new"


def test_get_alias_returns_none_for_missing(afile):
    assert get_alias("ghost", afile) is None


def test_remove_alias_returns_true(afile):
    set_alias("a", "job:a", afile)
    assert remove_alias("a", afile) is True
    assert get_alias("a", afile) is None


def test_remove_alias_returns_false_when_absent(afile):
    assert remove_alias("missing", afile) is False


def test_resolve_known_alias(afile):
    set_alias("short", "job:long-name", afile)
    assert resolve("short", afile) == "job:long-name"


def test_resolve_unknown_falls_back_to_name(afile):
    assert resolve("unknown", afile) == "unknown"


def test_all_aliases_empty(afile):
    assert all_aliases(afile) == {}


def test_all_aliases_multiple(afile):
    set_alias("a", "job:a", afile)
    set_alias("b", "job:b", afile)
    assert len(all_aliases(afile)) == 2


# --- CLI tests ---

def test_build_alias_parser_returns_parser():
    p = build_alias_parser()
    assert p is not None


def test_no_subcommand_returns_1(afile):
    assert _run([], afile) == 1


def test_set_exits_0(afile):
    assert _run(["set", "myalias", "job:target"], afile) == 0


def test_get_exits_0(afile):
    set_alias("myalias", "job:target", afile)
    assert _run(["get", "myalias"], afile) == 0


def test_get_missing_exits_1(afile):
    assert _run(["get", "ghost"], afile) == 1


def test_remove_exits_0(afile):
    set_alias("gone", "job:gone", afile)
    assert _run(["remove", "gone"], afile) == 0


def test_remove_missing_exits_1(afile):
    assert _run(["remove", "nope"], afile) == 1


def test_list_exits_0(afile):
    assert _run(["list"], afile) == 0


def test_resolve_exits_0(afile):
    assert _run(["resolve", "anything"], afile) == 0
