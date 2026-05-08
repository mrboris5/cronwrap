"""Tests for cronwrap.bookmark and cronwrap.bookmark_cli."""

from __future__ import annotations

import json
import pytest

from cronwrap.bookmark import (
    add_bookmark,
    get_bookmark,
    list_bookmarks,
    load_bookmarks,
    remove_bookmark,
    save_bookmarks,
)
from cronwrap.bookmark_cli import bookmark_main, build_bookmark_parser


@pytest.fixture()
def bfile(tmp_path):
    return str(tmp_path / "bookmarks.json")


def _run(argv, bfile):
    return bookmark_main(["--file", bfile] + argv)


# --- module tests ---

def test_load_bookmarks_missing_file(bfile):
    assert load_bookmarks(bfile) == {}


def test_load_bookmarks_corrupt_file(bfile):
    open(bfile, "w").write("not json")
    assert load_bookmarks(bfile) == {}


def test_save_and_load_roundtrip(bfile):
    data = {"job1": [{"name": "pos", "value": "42"}]}
    save_bookmarks(data, bfile)
    assert load_bookmarks(bfile) == data


def test_save_trims_to_max_entries(bfile):
    data = {"job1": [{"name": str(i), "value": str(i)} for i in range(10)]}
    save_bookmarks(data, bfile, max_entries=3)
    loaded = load_bookmarks(bfile)
    assert len(loaded["job1"]) == 3
    assert loaded["job1"][-1]["name"] == "9"


def test_add_bookmark_creates_entry(bfile):
    entry = add_bookmark("job1", "cursor", "100", bfile)
    assert entry["name"] == "cursor"
    assert entry["value"] == "100"


def test_add_bookmark_persists(bfile):
    add_bookmark("job1", "cursor", "55", bfile)
    data = load_bookmarks(bfile)
    assert data["job1"][0]["value"] == "55"


def test_get_bookmark_returns_value(bfile):
    add_bookmark("job1", "pos", "7", bfile)
    assert get_bookmark("job1", "pos", bfile) == "7"


def test_get_bookmark_returns_latest(bfile):
    add_bookmark("job1", "pos", "1", bfile)
    add_bookmark("job1", "pos", "2", bfile)
    assert get_bookmark("job1", "pos", bfile) == "2"


def test_get_bookmark_missing_returns_none(bfile):
    assert get_bookmark("job1", "missing", bfile) is None


def test_remove_bookmark_returns_true(bfile):
    add_bookmark("job1", "pos", "5", bfile)
    assert remove_bookmark("job1", "pos", bfile) is True


def test_remove_bookmark_missing_returns_false(bfile):
    assert remove_bookmark("job1", "ghost", bfile) is False


def test_list_bookmarks_empty(bfile):
    assert list_bookmarks("job1", bfile) == []


def test_list_bookmarks_returns_all(bfile):
    add_bookmark("job1", "a", "1", bfile)
    add_bookmark("job1", "b", "2", bfile)
    entries = list_bookmarks("job1", bfile)
    assert len(entries) == 2


# --- CLI tests ---

def test_build_bookmark_parser_returns_parser(bfile):
    p = build_bookmark_parser(bfile)
    assert p is not None


def test_no_subcommand_returns_1(bfile):
    assert _run([], bfile) == 1


def test_add_exits_0(bfile):
    assert _run(["add", "job1", "cursor", "99"], bfile) == 0


def test_get_exits_0(bfile):
    _run(["add", "job1", "cursor", "42"], bfile)
    assert _run(["get", "job1", "cursor"], bfile) == 0


def test_get_missing_exits_1(bfile):
    assert _run(["get", "job1", "nope"], bfile) == 1


def test_remove_exits_0(bfile):
    _run(["add", "job1", "cursor", "1"], bfile)
    assert _run(["remove", "job1", "cursor"], bfile) == 0


def test_list_exits_0(bfile):
    assert _run(["list", "job1"], bfile) == 0
