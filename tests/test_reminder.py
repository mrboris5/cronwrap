"""Tests for cronwrap.reminder."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwrap.reminder import (
    add_reminder,
    acknowledge_reminder,
    due_reminders,
    get_reminders,
    load_reminders,
    save_reminders,
)


@pytest.fixture()
def rfile(tmp_path: Path) -> str:
    return str(tmp_path / "reminders.json")


def _future() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


def _past() -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_reminders_missing_file(rfile: str) -> None:
    assert load_reminders(rfile) == {}


def test_load_reminders_corrupt_file(rfile: str) -> None:
    Path(rfile).write_text("not json")
    assert load_reminders(rfile) == {}


def test_save_and_load_roundtrip(rfile: str) -> None:
    data = {"job1": [{"message": "hi", "remind_at": _future()}]}
    save_reminders(rfile, data)
    assert load_reminders(rfile) == data


def test_save_trims_to_max_entries(rfile: str) -> None:
    entries = [{"message": str(i), "remind_at": _future()} for i in range(300)]
    save_reminders(rfile, {"job1": entries})
    loaded = load_reminders(rfile)
    assert len(loaded["job1"]) == 200


# ---------------------------------------------------------------------------
# add_reminder
# ---------------------------------------------------------------------------

def test_add_reminder_creates_entry(rfile: str) -> None:
    entry = add_reminder(rfile, "job1", "check logs", _future())
    assert entry["job_id"] == "job1"
    assert entry["message"] == "check logs"
    assert entry["acknowledged"] is False


def test_add_reminder_persists(rfile: str) -> None:
    add_reminder(rfile, "job1", "msg", _future())
    reminders = get_reminders(rfile, "job1")
    assert len(reminders) == 1


def test_add_multiple_reminders(rfile: str) -> None:
    add_reminder(rfile, "job1", "first", _future())
    add_reminder(rfile, "job1", "second", _future())
    assert len(get_reminders(rfile, "job1")) == 2


# ---------------------------------------------------------------------------
# acknowledge_reminder
# ---------------------------------------------------------------------------

def test_acknowledge_reminder_sets_flag(rfile: str) -> None:
    add_reminder(rfile, "job1", "msg", _future())
    result = acknowledge_reminder(rfile, "job1", 0)
    assert result is True
    reminders = get_reminders(rfile, "job1")
    assert reminders[0]["acknowledged"] is True
    assert "acknowledged_at" in reminders[0]


def test_acknowledge_reminder_invalid_index(rfile: str) -> None:
    add_reminder(rfile, "job1", "msg", _future())
    assert acknowledge_reminder(rfile, "job1", 99) is False


def test_acknowledge_reminder_missing_job(rfile: str) -> None:
    assert acknowledge_reminder(rfile, "ghost", 0) is False


# ---------------------------------------------------------------------------
# get_reminders / pending_only
# ---------------------------------------------------------------------------

def test_get_reminders_pending_only(rfile: str) -> None:
    add_reminder(rfile, "job1", "ack me", _future())
    add_reminder(rfile, "job1", "keep me", _future())
    acknowledge_reminder(rfile, "job1", 0)
    pending = get_reminders(rfile, "job1", pending_only=True)
    assert len(pending) == 1
    assert pending[0]["message"] == "keep me"


# ---------------------------------------------------------------------------
# due_reminders
# ---------------------------------------------------------------------------

def test_due_reminders_returns_past(rfile: str) -> None:
    add_reminder(rfile, "job1", "overdue", _past())
    add_reminder(rfile, "job1", "not yet", _future())
    due = due_reminders(rfile)
    assert len(due) == 1
    assert due[0]["message"] == "overdue"


def test_due_reminders_excludes_acknowledged(rfile: str) -> None:
    add_reminder(rfile, "job1", "done", _past())
    acknowledge_reminder(rfile, "job1", 0)
    assert due_reminders(rfile) == []
