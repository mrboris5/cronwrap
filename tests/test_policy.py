"""Tests for cronwrap.policy."""

import json
import pytest
from pathlib import Path

from cronwrap.policy import (
    apply_policy,
    get_policy,
    list_policies,
    load_policies,
    remove_policy,
    save_policies,
    set_policy,
)


@pytest.fixture()
def pfile(tmp_path: Path) -> Path:
    return tmp_path / "policies.json"


def test_load_policies_missing_file(pfile):
    assert load_policies(pfile) == {}


def test_load_policies_corrupt_file(pfile):
    pfile.write_text("not-json")
    assert load_policies(pfile) == {}


def test_save_and_load_roundtrip(pfile):
    data = {"nightly": {"retries": 3, "timeout": "1h"}}
    save_policies(data, pfile)
    assert load_policies(pfile) == data


def test_set_policy_creates_entry(pfile):
    rules = {"retries": 2, "alert": True}
    result = set_policy("default", rules, pfile)
    assert result == rules
    assert get_policy("default", pfile) == rules


def test_set_policy_replaces_existing(pfile):
    set_policy("p", {"retries": 1}, pfile)
    set_policy("p", {"retries": 5}, pfile)
    assert get_policy("p", pfile)["retries"] == 5


def test_get_policy_missing_returns_none(pfile):
    assert get_policy("ghost", pfile) is None


def test_remove_policy_existing(pfile):
    set_policy("tmp", {"x": 1}, pfile)
    assert remove_policy("tmp", pfile) is True
    assert get_policy("tmp", pfile) is None


def test_remove_policy_missing_returns_false(pfile):
    assert remove_policy("ghost", pfile) is False


def test_list_policies_empty(pfile):
    assert list_policies(pfile) == []


def test_list_policies_sorted(pfile):
    for name in ["zebra", "alpha", "mango"]:
        set_policy(name, {}, pfile)
    assert list_policies(pfile) == ["alpha", "mango", "zebra"]


def test_apply_policy_merges(pfile):
    set_policy("base", {"retries": 3, "timeout": "30m", "alert": False}, pfile)
    merged = apply_policy("base", {"alert": True, "command": "echo hi"}, pfile)
    assert merged["retries"] == 3
    assert merged["timeout"] == "30m"
    assert merged["alert"] is True        # job_cfg overrides policy
    assert merged["command"] == "echo hi"


def test_apply_policy_missing_raises(pfile):
    with pytest.raises(KeyError, match="not found"):
        apply_policy("ghost", {}, pfile)


def test_apply_policy_job_cfg_wins(pfile):
    set_policy("p", {"retries": 1}, pfile)
    merged = apply_policy("p", {"retries": 9}, pfile)
    assert merged["retries"] == 9
