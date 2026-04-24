"""Tests for cronwrap.runbook."""

import json
import pytest

from cronwrap.runbook import (
    get_runbook,
    list_runbooks,
    load_runbooks,
    remove_runbook,
    save_runbooks,
    set_runbook,
)


@pytest.fixture()
def rb_file(tmp_path):
    return str(tmp_path / "runbooks.json")


def test_load_runbooks_missing_file(rb_file):
    assert load_runbooks(rb_file) == {}


def test_load_runbooks_corrupt_file(rb_file):
    with open(rb_file, "w") as f:
        f.write("not json{{{")
    assert load_runbooks(rb_file) == {}


def test_save_and_load_roundtrip(rb_file):
    data = {"job1": {"url": "http://example.com"}}
    save_runbooks(rb_file, data)
    assert load_runbooks(rb_file) == data


def test_set_runbook_creates_entry(rb_file):
    entry = set_runbook(rb_file, "backup", url="http://wiki/backup", owner="alice")
    assert entry["url"] == "http://wiki/backup"
    assert entry["owner"] == "alice"


def test_set_runbook_updates_existing(rb_file):
    set_runbook(rb_file, "backup", url="http://old")
    set_runbook(rb_file, "backup", url="http://new", notes="updated")
    entry = get_runbook(rb_file, "backup")
    assert entry["url"] == "http://new"
    assert entry["notes"] == "updated"


def test_set_runbook_partial_update_preserves_fields(rb_file):
    set_runbook(rb_file, "job", url="http://x", owner="bob")
    set_runbook(rb_file, "job", notes="some notes")
    entry = get_runbook(rb_file, "job")
    assert entry["url"] == "http://x"
    assert entry["owner"] == "bob"
    assert entry["notes"] == "some notes"


def test_get_runbook_missing_returns_none(rb_file):
    assert get_runbook(rb_file, "nonexistent") is None


def test_remove_runbook_existing(rb_file):
    set_runbook(rb_file, "job", url="http://x")
    assert remove_runbook(rb_file, "job") is True
    assert get_runbook(rb_file, "job") is None


def test_remove_runbook_nonexistent(rb_file):
    assert remove_runbook(rb_file, "ghost") is False


def test_list_runbooks_empty(rb_file):
    assert list_runbooks(rb_file) == []


def test_list_runbooks_returns_all_ids(rb_file):
    set_runbook(rb_file, "job_a", url="http://a")
    set_runbook(rb_file, "job_b", owner="carol")
    ids = list_runbooks(rb_file)
    assert set(ids) == {"job_a", "job_b"}


def test_set_runbook_escalation_contact(rb_file):
    entry = set_runbook(rb_file, "alert_job", escalation_contact="oncall@example.com")
    assert entry["escalation_contact"] == "oncall@example.com"
