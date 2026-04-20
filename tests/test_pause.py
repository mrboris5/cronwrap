"""Tests for cronwrap.pause."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from cronwrap.pause import (
    is_paused,
    load_paused,
    pause_job,
    pause_reason,
    resume_job,
    save_paused,
)


@pytest.fixture()
def pfile(tmp_path):
    return str(tmp_path / "paused.json")


def test_load_paused_missing_file(pfile):
    assert load_paused(pfile) == {}


def test_load_paused_corrupt_file(pfile):
    with open(pfile, "w") as fh:
        fh.write("not json")
    assert load_paused(pfile) == {}


def test_save_and_load_roundtrip(pfile):
    data = {"job_a": {"paused_at": "2024-01-01T00:00:00+00:00", "expires": None}}
    save_paused(data, pfile)
    assert load_paused(pfile) == data


def test_pause_job_creates_entry(pfile):
    entry = pause_job("backup", path=pfile)
    assert "paused_at" in entry
    assert entry["expires"] is None
    stored = load_paused(pfile)
    assert "backup" in stored


def test_pause_job_with_expiry(pfile):
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    entry = pause_job("sync", expires=future, path=pfile)
    assert entry["expires"] == future


def test_is_paused_true_for_paused_job(pfile):
    pause_job("cleanup", path=pfile)
    assert is_paused("cleanup", pfile) is True


def test_is_paused_false_for_unknown_job(pfile):
    assert is_paused("nonexistent", pfile) is False


def test_is_paused_false_after_expiry(pfile):
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    pause_job("expired_job", expires=past, path=pfile)
    assert is_paused("expired_job", pfile) is False


def test_is_paused_true_before_expiry(pfile):
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    pause_job("future_job", expires=future, path=pfile)
    assert is_paused("future_job", pfile) is True


def test_resume_job_removes_entry(pfile):
    pause_job("report", path=pfile)
    removed = resume_job("report", pfile)
    assert removed is True
    assert is_paused("report", pfile) is False


def test_resume_job_returns_false_if_not_paused(pfile):
    assert resume_job("ghost", pfile) is False


def test_pause_reason_indefinite(pfile):
    pause_job("myjob", path=pfile)
    reason = pause_reason("myjob", pfile)
    assert "myjob" in reason
    assert "indefinitely" in reason


def test_pause_reason_with_expiry(pfile):
    future = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    pause_job("myjob2", expires=future, path=pfile)
    reason = pause_reason("myjob2", pfile)
    assert "expires" in reason


def test_pause_reason_empty_when_not_paused(pfile):
    assert pause_reason("active_job", pfile) == ""
