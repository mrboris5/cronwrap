"""Tests for cronwrap.event and cronwrap.event_cli."""

import json
import pytest

from cronwrap.event import (
    clear_events,
    get_events,
    load_events,
    record_event,
    save_events,
)
from cronwrap.event_cli import build_event_parser, event_main


@pytest.fixture()
def efile(tmp_path):
    return str(tmp_path / "events.json")


# --- module tests ---

def test_load_events_missing_file(efile):
    assert load_events(efile) == {}


def test_load_events_corrupt_file(efile):
    open(efile, "w").write("not-json")
    assert load_events(efile) == {}


def test_save_and_load_roundtrip(efile):
    data = {"job1": [{"timestamp": "t", "event_type": "start", "message": "hi"}]}
    save_events(data, efile)
    assert load_events(efile) == data


def test_save_trims_to_max_entries(efile):
    data = {"job1": [{"event_type": "x", "message": str(i)} for i in range(10)]}
    save_events(data, efile, max_entries=3)
    loaded = load_events(efile)
    assert len(loaded["job1"]) == 3


def test_record_event_creates_entry(efile):
    entry = record_event("job1", "success", "all good", efile)
    assert entry["event_type"] == "success"
    assert entry["message"] == "all good"
    assert "timestamp" in entry


def test_record_event_persists(efile):
    record_event("job1", "start", "beginning", efile)
    record_event("job1", "end", "done", efile)
    events = get_events("job1", efile)
    assert len(events) == 2


def test_record_event_extra_fields(efile):
    entry = record_event("job1", "info", "note", efile, extra={"code": 42})
    assert entry["code"] == 42


def test_get_events_filter_by_type(efile):
    record_event("job1", "start", "s", efile)
    record_event("job1", "error", "e", efile)
    errors = get_events("job1", efile, event_type="error")
    assert len(errors) == 1
    assert errors[0]["event_type"] == "error"


def test_get_events_limit(efile):
    for i in range(10):
        record_event("job1", "tick", str(i), efile)
    events = get_events("job1", efile, limit=3)
    assert len(events) == 3


def test_clear_events_removes_entries(efile):
    record_event("job1", "x", "m", efile)
    n = clear_events("job1", efile)
    assert n == 1
    assert get_events("job1", efile) == []


def test_clear_events_missing_job(efile):
    assert clear_events("ghost", efile) == 0


# --- CLI tests ---

def _run(argv):
    return event_main(argv)


def test_build_event_parser_returns_parser(efile):
    p = build_event_parser()
    assert p is not None


def test_no_subcommand_returns_1(efile):
    assert _run(["--file", efile]) == 1


def test_record_exits_0(efile):
    assert _run(["--file", efile, "record", "job1", "start", "hello"]) == 0


def test_list_exits_0(efile):
    record_event("job1", "info", "hi", efile)
    assert _run(["--file", efile, "list", "job1"]) == 0


def test_clear_exits_0(efile):
    record_event("job1", "info", "hi", efile)
    assert _run(["--file", efile, "clear", "job1"]) == 0
