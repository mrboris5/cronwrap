"""Tests for cronwrap.profile and cronwrap.profile_cli."""

import json
import os
import pytest

from cronwrap.profile import (
    clear_profile,
    load_profiles,
    profile_stats,
    record_duration,
    save_profiles,
)
from cronwrap.profile_cli import build_profile_parser, profile_main


@pytest.fixture
def pfile(tmp_path):
    return str(tmp_path / "profiles.json")


def test_load_profiles_missing_file(pfile):
    assert load_profiles(pfile) == {}


def test_load_profiles_corrupt_file(pfile):
    with open(pfile, "w") as f:
        f.write("not json")
    assert load_profiles(pfile) == {}


def test_save_and_load_roundtrip(pfile):
    save_profiles(pfile, {"job1": [1.0, 2.0]})
    data = load_profiles(pfile)
    assert data == {"job1": [1.0, 2.0]}


def test_record_duration_creates_entry(pfile):
    record_duration(pfile, "job1", 3.5)
    data = load_profiles(pfile)
    assert "job1" in data
    assert data["job1"] == [3.5]


def test_record_duration_appends(pfile):
    record_duration(pfile, "job1", 1.0)
    record_duration(pfile, "job1", 2.0)
    data = load_profiles(pfile)
    assert len(data["job1"]) == 2


def test_record_duration_trims_to_max(pfile):
    for i in range(5):
        record_duration(pfile, "job1", float(i), max_samples=3)
    data = load_profiles(pfile)
    assert len(data["job1"]) == 3
    assert data["job1"] == [2.0, 3.0, 4.0]


def test_profile_stats_no_data(pfile):
    assert profile_stats(pfile, "missing") is None


def test_profile_stats_values(pfile):
    for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
        record_duration(pfile, "job1", v)
    stats = profile_stats(pfile, "job1")
    assert stats is not None
    assert stats["count"] == 5
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["avg"] == 3.0


def test_clear_profile_removes_entry(pfile):
    record_duration(pfile, "job1", 1.0)
    removed = clear_profile(pfile, "job1")
    assert removed is True
    assert load_profiles(pfile) == {}


def test_clear_profile_missing_returns_false(pfile):
    assert clear_profile(pfile, "ghost") is False


# --- CLI tests ---

def _run(argv, pfile):
    return profile_main(["--file", pfile] + argv)


def test_build_profile_parser_returns_parser(pfile):
    p = build_profile_parser()
    assert p is not None


def test_no_subcommand_returns_1(pfile):
    assert _run([], pfile) == 1


def test_show_no_data_returns_1(pfile):
    assert _run(["show", "job1"], pfile) == 1


def test_show_with_data_returns_0(pfile, capsys):
    record_duration(pfile, "job1", 2.5)
    rc = _run(["show", "job1"], pfile)
    assert rc == 0
    out = capsys.readouterr().out
    assert "job1" in out
    assert "Count" in out


def test_clear_existing_returns_0(pfile, capsys):
    record_duration(pfile, "job1", 1.0)
    rc = _run(["clear", "job1"], pfile)
    assert rc == 0


def test_clear_missing_returns_1(pfile):
    assert _run(["clear", "ghost"], pfile) == 1
