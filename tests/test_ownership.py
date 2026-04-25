"""Tests for cronwrap.ownership and cronwrap.ownership_cli."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwrap.ownership import (
    all_owners,
    get_owner,
    jobs_by_team,
    load_owners,
    remove_owner,
    set_owner,
)
from cronwrap.ownership_cli import ownership_main


@pytest.fixture()
def ofile(tmp_path: Path) -> Path:
    return tmp_path / "owners.json"


def _run(args: list[str], ofile: Path) -> int:
    return ownership_main(["--file", str(ofile)] + args)


# --- unit tests for ownership module ---

def test_load_owners_missing_file(ofile):
    assert load_owners(ofile) == {}


def test_load_owners_corrupt_file(ofile):
    ofile.write_text("not json")
    assert load_owners(ofile) == {}


def test_set_owner_creates_entry(ofile):
    entry = set_owner("job1", "alice", path=ofile)
    assert entry["owner"] == "alice"
    assert get_owner("job1", path=ofile) == {"owner": "alice"}


def test_set_owner_with_team_and_email(ofile):
    entry = set_owner("job2", "bob", team="ops", email="bob@example.com", path=ofile)
    assert entry["team"] == "ops"
    assert entry["email"] == "bob@example.com"


def test_set_owner_overwrites(ofile):
    set_owner("job1", "alice", path=ofile)
    set_owner("job1", "carol", team="dev", path=ofile)
    entry = get_owner("job1", path=ofile)
    assert entry["owner"] == "carol"
    assert entry["team"] == "dev"


def test_get_owner_missing_returns_none(ofile):
    assert get_owner("nope", path=ofile) is None


def test_remove_owner_returns_true(ofile):
    set_owner("job1", "alice", path=ofile)
    assert remove_owner("job1", path=ofile) is True
    assert get_owner("job1", path=ofile) is None


def test_remove_owner_missing_returns_false(ofile):
    assert remove_owner("ghost", path=ofile) is False


def test_jobs_by_team(ofile):
    set_owner("j1", "alice", team="ops", path=ofile)
    set_owner("j2", "bob", team="dev", path=ofile)
    set_owner("j3", "carol", team="ops", path=ofile)
    result = jobs_by_team("ops", path=ofile)
    assert set(result) == {"j1", "j3"}


def test_jobs_by_team_case_insensitive(ofile):
    set_owner("j1", "alice", team="OPS", path=ofile)
    assert "j1" in jobs_by_team("ops", path=ofile)


def test_all_owners_returns_all(ofile):
    set_owner("j1", "alice", path=ofile)
    set_owner("j2", "bob", path=ofile)
    data = all_owners(path=ofile)
    assert set(data.keys()) == {"j1", "j2"}


# --- CLI tests ---

def test_no_subcommand_returns_1(ofile):
    assert _run([], ofile) == 1


def test_cli_set_exits_0(ofile):
    assert _run(["set", "job1", "alice"], ofile) == 0


def test_cli_get_exits_0(ofile):
    _run(["set", "job1", "alice"], ofile)
    assert _run(["get", "job1"], ofile) == 0


def test_cli_get_missing_exits_1(ofile):
    assert _run(["get", "ghost"], ofile) == 1


def test_cli_remove_exits_0(ofile):
    _run(["set", "job1", "alice"], ofile)
    assert _run(["remove", "job1"], ofile) == 0


def test_cli_remove_missing_exits_1(ofile):
    assert _run(["remove", "ghost"], ofile) == 1


def test_cli_team_lists_jobs(ofile, capsys):
    _run(["set", "j1", "alice", "--team", "ops"], ofile)
    _run(["set", "j2", "bob", "--team", "dev"], ofile)
    _run(["team", "ops"], ofile)
    out = capsys.readouterr().out
    assert "j1" in out
    assert "j2" not in out


def test_cli_list_shows_all(ofile, capsys):
    _run(["set", "j1", "alice"], ofile)
    _run(["set", "j2", "bob"], ofile)
    _run(["list"], ofile)
    out = capsys.readouterr().out
    assert "j1" in out
    assert "j2" in out
