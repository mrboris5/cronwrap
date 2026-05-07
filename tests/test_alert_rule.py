"""Tests for cronwrap.alert_rule."""
import json
import pytest

from cronwrap.alert_rule import (
    evaluate_rule,
    get_alert_rule,
    list_rules,
    load_alert_rules,
    remove_alert_rule,
    set_alert_rule,
)


@pytest.fixture()
def rfile(tmp_path):
    return str(tmp_path / "rules.json")


def test_load_alert_rules_missing_file(rfile):
    assert load_alert_rules(rfile) == {}


def test_load_alert_rules_corrupt_file(rfile):
    with open(rfile, "w") as f:
        f.write("not json")
    assert load_alert_rules(rfile) == {}


def test_save_and_load_roundtrip(rfile):
    set_alert_rule(rfile, "job1", "gt", 5.0)
    rules = load_alert_rules(rfile)
    assert "job1" in rules
    assert rules["job1"]["condition"] == "gt"
    assert rules["job1"]["threshold"] == 5.0


def test_set_alert_rule_creates_entry(rfile):
    entry = set_alert_rule(rfile, "job2", "lt", 1.0, channel="slack")
    assert entry["condition"] == "lt"
    assert entry["channel"] == "slack"
    assert entry["enabled"] is True


def test_set_alert_rule_disabled(rfile):
    entry = set_alert_rule(rfile, "job3", "gte", 10.0, enabled=False)
    assert entry["enabled"] is False


def test_get_alert_rule_returns_entry(rfile):
    set_alert_rule(rfile, "job4", "eq", 0.0)
    rule = get_alert_rule(rfile, "job4")
    assert rule is not None
    assert rule["condition"] == "eq"


def test_get_alert_rule_missing_returns_none(rfile):
    assert get_alert_rule(rfile, "nonexistent") is None


def test_remove_alert_rule_returns_true(rfile):
    set_alert_rule(rfile, "job5", "gt", 3.0)
    assert remove_alert_rule(rfile, "job5") is True
    assert get_alert_rule(rfile, "job5") is None


def test_remove_alert_rule_missing_returns_false(rfile):
    assert remove_alert_rule(rfile, "ghost") is False


def test_list_rules_empty(rfile):
    assert list_rules(rfile) == []


def test_list_rules_returns_all(rfile):
    set_alert_rule(rfile, "a", "gt", 1.0)
    set_alert_rule(rfile, "b", "lt", 2.0)
    entries = list_rules(rfile)
    job_ids = {e["job_id"] for e in entries}
    assert job_ids == {"a", "b"}


@pytest.mark.parametrize("condition,value,expected", [
    ("gt", 6.0, True),
    ("gt", 5.0, False),
    ("lt", 4.0, True),
    ("lt", 5.0, False),
    ("gte", 5.0, True),
    ("lte", 5.0, True),
    ("eq", 5.0, True),
    ("eq", 4.9, False),
])
def test_evaluate_rule_conditions(condition, value, expected):
    rule = {"condition": condition, "threshold": 5.0, "enabled": True}
    assert evaluate_rule(rule, value) is expected


def test_evaluate_rule_disabled_returns_false():
    rule = {"condition": "gt", "threshold": 1.0, "enabled": False}
    assert evaluate_rule(rule, 999.0) is False


def test_evaluate_rule_unknown_condition_returns_false():
    rule = {"condition": "neq", "threshold": 1.0, "enabled": True}
    assert evaluate_rule(rule, 2.0) is False
