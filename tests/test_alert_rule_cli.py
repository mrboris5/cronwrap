"""Tests for cronwrap.alert_rule_cli."""
import pytest

from cronwrap.alert_rule import set_alert_rule
from cronwrap.alert_rule_cli import alert_rule_main, build_alert_rule_parser


@pytest.fixture()
def rf(tmp_path):
    return str(tmp_path / "rules.json")


def _run(rf, *args):
    return alert_rule_main(["--file", rf, *args])


def test_build_alert_rule_parser_returns_parser():
    p = build_alert_rule_parser()
    assert p is not None


def test_no_subcommand_returns_1(rf):
    assert alert_rule_main(["--file", rf]) == 1


def test_set_exits_0(rf):
    assert _run(rf, "set", "job1", "gt", "5.0") == 0


def test_set_with_channel(rf):
    assert _run(rf, "set", "job2", "lt", "2.0", "--channel", "slack") == 0


def test_set_disabled(rf):
    assert _run(rf, "set", "job3", "gte", "1.0", "--disabled") == 0


def test_get_exits_0(rf):
    set_alert_rule(rf, "job4", "eq", 0.0)
    assert _run(rf, "get", "job4") == 0


def test_get_missing_exits_1(rf):
    assert _run(rf, "get", "ghost") == 1


def test_remove_exits_0(rf):
    set_alert_rule(rf, "job5", "gt", 3.0)
    assert _run(rf, "remove", "job5") == 0


def test_remove_missing_exits_1(rf):
    assert _run(rf, "remove", "nobody") == 1


def test_list_exits_0(rf):
    assert _run(rf, "list") == 0


def test_eval_triggered(rf):
    set_alert_rule(rf, "job6", "gt", 5.0)
    assert _run(rf, "eval", "job6", "10.0") == 0


def test_eval_missing_rule_exits_1(rf):
    assert _run(rf, "eval", "ghost", "1.0") == 1
