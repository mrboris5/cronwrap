"""Tests for cronwrap.watchdog."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from cronwrap.watchdog import (
    load_watchdog,
    save_watchdog,
    register_watchdog,
    checkin,
    is_overdue,
    overdue_reason,
    _parse_seconds,
)


@pytest.fixture
def wfile(tmp_path):
    return str(tmp_path / "watchdog.json")


def test_load_watchdog_missing_file(wfile):
    assert load_watchdog(wfile) == {}


def test_load_watchdog_corrupt_file(wfile):
    Path(wfile).write_text("not json")
    assert load_watchdog(wfile) == {}


def test_save_and_load_roundtrip(wfile):
    data = {"job1": {"interval": "1h", "grace": "5m", "last_seen": None}}
    save_watchdog(wfile, data)
    assert load_watchdog(wfile) == data


def test_register_watchdog_creates_entry(wfile):
    entry = register_watchdog(wfile, "myjob", "30m")
    assert entry["interval"] == "30m"
    assert entry["grace"] == "5m"
    assert entry["last_seen"] is None
    assert "registered_at" in entry


def test_register_watchdog_custom_grace(wfile):
    entry = register_watchdog(wfile, "myjob", "1h", grace="10m")
    assert entry["grace"] == "10m"


def test_register_watchdog_persists(wfile):
    register_watchdog(wfile, "myjob", "1h")
    state = load_watchdog(wfile)
    assert "myjob" in state


def test_checkin_updates_last_seen(wfile):
    register_watchdog(wfile, "myjob", "1h")
    entry = checkin(wfile, "myjob")
    assert entry["last_seen"] is not None


def test_checkin_unknown_job_creates_entry(wfile):
    entry = checkin(wfile, "newjob")
    assert entry["last_seen"] is not None


def test_parse_seconds_s():
    assert _parse_seconds("30s") == 30


def test_parse_seconds_m():
    assert _parse_seconds("5m") == 300


def test_parse_seconds_h():
    assert _parse_seconds("2h") == 7200


def test_parse_seconds_d():
    assert _parse_seconds("1d") == 86400


def test_is_overdue_false_when_recent(wfile):
    register_watchdog(wfile, "myjob", "1h", grace="5m")
    checkin(wfile, "myjob")
    assert is_overdue(wfile, "myjob") is False


def test_is_overdue_true_when_stale(wfile):
    register_watchdog(wfile, "myjob", "1m", grace="0s")
    state = load_watchdog(wfile)
    stale_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    state["myjob"]["last_seen"] = stale_time
    save_watchdog(wfile, state)
    assert is_overdue(wfile, "myjob") is True


def test_is_overdue_false_no_interval(wfile):
    checkin(wfile, "myjob")
    assert is_overdue(wfile, "myjob") is False


def test_overdue_reason_none_when_ok(wfile):
    register_watchdog(wfile, "myjob", "1h")
    checkin(wfile, "myjob")
    assert overdue_reason(wfile, "myjob") is None


def test_overdue_reason_string_when_overdue(wfile):
    register_watchdog(wfile, "myjob", "1m", grace="0s")
    state = load_watchdog(wfile)
    stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    state["myjob"]["last_seen"] = stale
    save_watchdog(wfile, state)
    reason = overdue_reason(wfile, "myjob")
    assert reason is not None
    assert "myjob" in reason
    assert "1m" in reason
