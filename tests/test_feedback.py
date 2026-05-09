"""Tests for cronwrap.feedback and cronwrap.feedback_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwrap.feedback import (
    add_feedback,
    average_rating,
    get_feedback,
    load_feedback,
    remove_feedback,
    save_feedback,
)
from cronwrap.feedback_cli import build_feedback_parser, feedback_main


@pytest.fixture()
def ffile(tmp_path: Path) -> str:
    return str(tmp_path / "feedback.json")


def _run(args: list[str], ffile: str) -> int:
    return feedback_main(["--file", ffile] + args)


# --- module tests ---

def test_load_feedback_missing_file(ffile):
    assert load_feedback(ffile) == {}


def test_load_feedback_corrupt_file(ffile):
    Path(ffile).write_text("not json")
    assert load_feedback(ffile) == {}


def test_save_and_load_roundtrip(ffile):
    data = {"job1": [{"run_id": "r1", "rating": 4, "comment": "", "author": "", "timestamp": "t"}]}
    save_feedback(ffile, data)
    assert load_feedback(ffile) == data


def test_add_feedback_creates_entry(ffile):
    entry = add_feedback(ffile, "job1", "run-abc", 5, comment="great", author="alice")
    assert entry["rating"] == 5
    assert entry["comment"] == "great"
    assert entry["author"] == "alice"
    assert entry["run_id"] == "run-abc"
    assert "timestamp" in entry


def test_add_feedback_persists(ffile):
    add_feedback(ffile, "job1", "r1", 3)
    entries = get_feedback(ffile, "job1")
    assert len(entries) == 1
    assert entries[0]["rating"] == 3


def test_add_feedback_clamps_rating_low(ffile):
    entry = add_feedback(ffile, "job1", "r1", 0)
    assert entry["rating"] == 1


def test_add_feedback_clamps_rating_high(ffile):
    entry = add_feedback(ffile, "job1", "r1", 99)
    assert entry["rating"] == 5


def test_get_feedback_missing_job(ffile):
    assert get_feedback(ffile, "no-such-job") == []


def test_average_rating_no_entries(ffile):
    assert average_rating(ffile, "job1") is None


def test_average_rating_single(ffile):
    add_feedback(ffile, "job1", "r1", 4)
    assert average_rating(ffile, "job1") == pytest.approx(4.0)


def test_average_rating_multiple(ffile):
    add_feedback(ffile, "job1", "r1", 2)
    add_feedback(ffile, "job1", "r2", 4)
    assert average_rating(ffile, "job1") == pytest.approx(3.0)


def test_remove_feedback_returns_true(ffile):
    add_feedback(ffile, "job1", "r1", 3)
    assert remove_feedback(ffile, "job1", "r1") is True
    assert get_feedback(ffile, "job1") == []


def test_remove_feedback_missing_returns_false(ffile):
    assert remove_feedback(ffile, "job1", "no-such-run") is False


# --- CLI tests ---

def test_build_feedback_parser_returns_parser(ffile):
    p = build_feedback_parser(ffile)
    assert p is not None


def test_no_subcommand_returns_1(ffile):
    assert _run([], ffile) == 1


def test_add_exits_0(ffile):
    assert _run(["add", "job1", "run1", "5", "--comment", "nice"], ffile) == 0


def test_show_exits_0(ffile):
    assert _run(["show", "job1"], ffile) == 0


def test_avg_exits_0(ffile):
    _run(["add", "job1", "r1", "4"], ffile)
    assert _run(["avg", "job1"], ffile) == 0


def test_remove_exits_0(ffile):
    _run(["add", "job1", "r1", "3"], ffile)
    assert _run(["remove", "job1", "r1"], ffile) == 0


def test_remove_missing_exits_1(ffile):
    assert _run(["remove", "job1", "no-run"], ffile) == 1
