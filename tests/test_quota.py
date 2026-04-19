"""Tests for cronwrap.quota."""

from __future__ import annotations

import pytest

from cronwrap.quota import (
    load_quotas,
    save_quotas,
    increment_quota,
    reset_quota,
    reset_all_quotas,
    quota_exceeded,
    quota_status,
)


@pytest.fixture
def qfile(tmp_path):
    return str(tmp_path / "quotas.json")


def test_load_quotas_missing_file(qfile):
    assert load_quotas(qfile) == {}


def test_load_quotas_corrupt_file(qfile):
    with open(qfile, "w") as f:
        f.write("not-json")
    assert load_quotas(qfile) == {}


def test_save_and_load_roundtrip(qfile):
    save_quotas(qfile, {"job1": 3, "job2": 7})
    data = load_quotas(qfile)
    assert data["job1"] == 3
    assert data["job2"] == 7


def test_increment_quota_starts_at_one(qfile):
    count = increment_quota(qfile, "myjob")
    assert count == 1


def test_increment_quota_accumulates(qfile):
    increment_quota(qfile, "myjob")
    increment_quota(qfile, "myjob")
    count = increment_quota(qfile, "myjob")
    assert count == 3


def test_increment_quota_independent_jobs(qfile):
    increment_quota(qfile, "job_a")
    increment_quota(qfile, "job_a")
    increment_quota(qfile, "job_b")
    assert load_quotas(qfile)["job_a"] == 2
    assert load_quotas(qfile)["job_b"] == 1


def test_reset_quota(qfile):
    increment_quota(qfile, "myjob")
    increment_quota(qfile, "myjob")
    reset_quota(qfile, "myjob")
    assert load_quotas(qfile)["myjob"] == 0


def test_reset_all_quotas(qfile):
    increment_quota(qfile, "job1")
    increment_quota(qfile, "job2")
    reset_all_quotas(qfile)
    assert load_quotas(qfile) == {}


def test_quota_exceeded_true(qfile):
    for _ in range(5):
        increment_quota(qfile, "myjob")
    assert quota_exceeded(qfile, "myjob", limit=5) is True


def test_quota_exceeded_false(qfile):
    increment_quota(qfile, "myjob")
    assert quota_exceeded(qfile, "myjob", limit=5) is False


def test_quota_status_string(qfile):
    increment_quota(qfile, "myjob")
    increment_quota(qfile, "myjob")
    status = quota_status(qfile, "myjob", limit=10)
    assert "myjob" in status
    assert "2/10" in status
