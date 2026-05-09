"""Tests for cronwrap.blackout and cronwrap.blackout_cli."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.blackout import (
    add_blackout,
    blackout_reason,
    get_blackouts,
    is_blacked_out,
    load_blackouts,
    remove_blackout,
    save_blackouts,
)
from cronwrap.blackout_cli import blackout_main, build_blackout_parser


@pytest.fixture
def bfile(tmp_path) -> str:
    return str(tmp_path / "blackouts.json")


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- blackout module ---

def test_load_blackouts_missing_file(bfile):
    assert load_blackouts(bfile) == {}


def test_load_blackouts_corrupt_file(bfile):
    Path(bfile).write_text("not json")
    assert load_blackouts(bfile) == {}


def test_save_and_load_roundtrip(bfile):
    data = {"job1": [{"start": "a", "end": "b", "reason": "", "created_at": "c"}]}
    save_blackouts(bfile, data)
    assert load_blackouts(bfile) == data


def test_add_blackout_creates_entry(bfile):
    now = _utcnow()
    start = _iso(now)
    end = _iso(now + timedelta(hours=2))
    entry = add_blackout(bfile, "myjob", start, end, reason="maintenance")
    assert entry["start"] == start
    assert entry["end"] == end
    assert entry["reason"] == "maintenance"
    assert "created_at" in entry


def test_add_blackout_persists(bfile):
    now = _utcnow()
    start = _iso(now)
    end = _iso(now + timedelta(hours=1))
    add_blackout(bfile, "myjob", start, end)
    windows = get_blackouts(bfile, "myjob")
    assert len(windows) == 1


def test_get_blackouts_empty(bfile):
    assert get_blackouts(bfile, "unknown") == []


def test_remove_blackout_success(bfile):
    now = _utcnow()
    add_blackout(bfile, "j", _iso(now), _iso(now + timedelta(hours=1)))
    add_blackout(bfile, "j", _iso(now), _iso(now + timedelta(hours=2)))
    ok = remove_blackout(bfile, "j", 0)
    assert ok is True
    assert len(get_blackouts(bfile, "j")) == 1


def test_remove_blackout_invalid_index(bfile):
    assert remove_blackout(bfile, "j", 5) is False


def test_is_blacked_out_true(bfile):
    now = _utcnow()
    add_blackout(bfile, "j", _iso(now - timedelta(hours=1)), _iso(now + timedelta(hours=1)))
    assert is_blacked_out(bfile, "j") is True


def test_is_blacked_out_false(bfile):
    now = _utcnow()
    add_blackout(bfile, "j", _iso(now + timedelta(hours=1)), _iso(now + timedelta(hours=2)))
    assert is_blacked_out(bfile, "j") is False


def test_blackout_reason_returns_message(bfile):
    now = _utcnow()
    add_blackout(bfile, "j", _iso(now - timedelta(hours=1)), _iso(now + timedelta(hours=1)), reason="freeze")
    msg = blackout_reason(bfile, "j")
    assert "Blacked out" in msg
    assert "freeze" in msg


def test_blackout_reason_empty_when_not_blacked_out(bfile):
    assert blackout_reason(bfile, "j") == ""


# --- CLI ---

def _run(bfile, *args):
    return blackout_main(["--file", bfile] + list(args))


def test_build_blackout_parser_returns_parser(bfile):
    assert build_blackout_parser() is not None


def test_no_subcommand_returns_1(bfile):
    assert _run(bfile) == 1


def test_add_exits_0(bfile):
    now = _utcnow()
    rc = _run(bfile, "add", "myjob", _iso(now), _iso(now + timedelta(hours=1)), "--reason", "test")
    assert rc == 0


def test_list_exits_0(bfile):
    assert _run(bfile, "list", "myjob") == 0


def test_remove_exits_0(bfile):
    now = _utcnow()
    _run(bfile, "add", "myjob", _iso(now), _iso(now + timedelta(hours=1)))
    assert _run(bfile, "remove", "myjob", "0") == 0


def test_remove_invalid_index_returns_1(bfile):
    assert _run(bfile, "remove", "myjob", "99") == 1


def test_check_not_blacked_out_returns_0(bfile):
    assert _run(bfile, "check", "myjob") == 0


def test_check_blacked_out_returns_1(bfile):
    now = _utcnow()
    _run(bfile, "add", "myjob", _iso(now - timedelta(hours=1)), _iso(now + timedelta(hours=1)))
    assert _run(bfile, "check", "myjob") == 1
