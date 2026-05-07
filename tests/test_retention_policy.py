"""Tests for cronwrap.retention_policy."""
import json
import pytest

from cronwrap.retention_policy import (
    get_retention_policy,
    list_retention_policies,
    load_retention_policies,
    remove_retention_policy,
    save_retention_policies,
    set_retention_policy,
)


@pytest.fixture()
def pfile(tmp_path):
    return str(tmp_path / "ret_policies.json")


def test_load_retention_policies_missing_file(pfile):
    assert load_retention_policies(pfile) == {}


def test_load_retention_policies_corrupt_file(pfile):
    open(pfile, "w").write("not-json")
    assert load_retention_policies(pfile) == {}


def test_save_and_load_roundtrip(pfile):
    data = {"job1": {"max_count": 10}}
    save_retention_policies(pfile, data)
    assert load_retention_policies(pfile) == data


def test_set_retention_policy_creates_entry(pfile):
    entry = set_retention_policy(pfile, "job1", max_count=50)
    assert entry["max_count"] == 50
    assert get_retention_policy(pfile, "job1")["max_count"] == 50


def test_set_retention_policy_both_fields(pfile):
    entry = set_retention_policy(pfile, "job2", max_age_days=30, max_count=100)
    assert entry["max_age_days"] == 30
    assert entry["max_count"] == 100


def test_set_retention_policy_partial_update(pfile):
    set_retention_policy(pfile, "job3", max_count=20)
    set_retention_policy(pfile, "job3", max_age_days=7)
    policy = get_retention_policy(pfile, "job3")
    assert policy["max_count"] == 20
    assert policy["max_age_days"] == 7


def test_get_retention_policy_missing(pfile):
    assert get_retention_policy(pfile, "nonexistent") == {}


def test_remove_retention_policy_existing(pfile):
    set_retention_policy(pfile, "job4", max_count=5)
    removed = remove_retention_policy(pfile, "job4")
    assert removed is True
    assert get_retention_policy(pfile, "job4") == {}


def test_remove_retention_policy_nonexistent(pfile):
    assert remove_retention_policy(pfile, "ghost") is False


def test_list_retention_policies_sorted(pfile):
    set_retention_policy(pfile, "z_job", max_count=1)
    set_retention_policy(pfile, "a_job", max_count=2)
    items = list_retention_policies(pfile)
    assert items[0][0] == "a_job"
    assert items[1][0] == "z_job"


def test_list_retention_policies_empty(pfile):
    assert list_retention_policies(pfile) == []
