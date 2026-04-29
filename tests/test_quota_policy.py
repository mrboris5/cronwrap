"""Tests for cronwrap.quota_policy."""

import json
import pytest

from cronwrap.quota_policy import (
    get_quota,
    list_quotas,
    load_quota_policy,
    remove_quota,
    save_quota_policy,
    set_quota,
)


@pytest.fixture()
def qp_file(tmp_path):
    return str(tmp_path / "quota_policy.json")


def test_load_quota_policy_missing_file(qp_file):
    result = load_quota_policy(qp_file)
    assert result == {}


def test_load_quota_policy_corrupt_file(qp_file):
    with open(qp_file, "w") as f:
        f.write("not-json")
    result = load_quota_policy(qp_file)
    assert result == {}


def test_save_and_load_roundtrip(qp_file):
    data = {"job1": {"max_runs": 5, "period": "1h", "updated_at": "2024-01-01T00:00:00+00:00"}}
    save_quota_policy(data, qp_file)
    loaded = load_quota_policy(qp_file)
    assert loaded == data


def test_set_quota_creates_entry(qp_file):
    entry = set_quota("backup", 10, "24h", path=qp_file)
    assert entry["max_runs"] == 10
    assert entry["period"] == "24h"
    assert "updated_at" in entry


def test_set_quota_persists(qp_file):
    set_quota("backup", 10, "24h", path=qp_file)
    loaded = load_quota_policy(qp_file)
    assert "backup" in loaded
    assert loaded["backup"]["max_runs"] == 10


def test_set_quota_overwrites(qp_file):
    set_quota("backup", 10, "24h", path=qp_file)
    set_quota("backup", 3, "1h", path=qp_file)
    entry = get_quota("backup", path=qp_file)
    assert entry["max_runs"] == 3
    assert entry["period"] == "1h"


def test_get_quota_missing(qp_file):
    assert get_quota("nonexistent", path=qp_file) is None


def test_get_quota_existing(qp_file):
    set_quota("myjob", 5, "7d", path=qp_file)
    entry = get_quota("myjob", path=qp_file)
    assert entry is not None
    assert entry["max_runs"] == 5


def test_remove_quota_existing(qp_file):
    set_quota("myjob", 5, "7d", path=qp_file)
    result = remove_quota("myjob", path=qp_file)
    assert result is True
    assert get_quota("myjob", path=qp_file) is None


def test_remove_quota_missing(qp_file):
    result = remove_quota("ghost", path=qp_file)
    assert result is False


def test_list_quotas_empty(qp_file):
    assert list_quotas(qp_file) == {}


def test_list_quotas_multiple(qp_file):
    set_quota("job_a", 5, "1h", path=qp_file)
    set_quota("job_b", 20, "24h", path=qp_file)
    data = list_quotas(qp_file)
    assert "job_a" in data
    assert "job_b" in data
