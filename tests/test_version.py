"""Tests for cronwrap.version."""

import json
import pytest

from cronwrap.version import (
    all_versions,
    get_version,
    load_versions,
    remove_version,
    save_versions,
    set_version,
)


@pytest.fixture()
def vfile(tmp_path):
    return str(tmp_path / "versions.json")


def test_load_versions_missing_file(vfile):
    assert load_versions(vfile) == {}


def test_load_versions_corrupt_file(vfile):
    with open(vfile, "w") as f:
        f.write("not-json!!!")
    assert load_versions(vfile) == {}


def test_save_and_load_roundtrip(vfile):
    data = {"job-a": {"version": "1.0.0", "metadata": {}}}
    save_versions(vfile, data)
    assert load_versions(vfile) == data


def test_set_version_creates_entry(vfile):
    entry = set_version(vfile, "job-a", "2.3.1")
    assert entry["version"] == "2.3.1"
    assert entry["metadata"] == {}


def test_set_version_persists(vfile):
    set_version(vfile, "job-a", "0.9.0")
    loaded = load_versions(vfile)
    assert "job-a" in loaded
    assert loaded["job-a"]["version"] == "0.9.0"


def test_set_version_with_metadata(vfile):
    entry = set_version(vfile, "job-b", "1.1.0", metadata={"env": "prod"})
    assert entry["metadata"] == {"env": "prod"}


def test_set_version_overwrites_existing(vfile):
    set_version(vfile, "job-a", "1.0.0")
    set_version(vfile, "job-a", "1.0.1")
    assert get_version(vfile, "job-a")["version"] == "1.0.1"


def test_get_version_returns_entry(vfile):
    set_version(vfile, "job-c", "3.0.0")
    entry = get_version(vfile, "job-c")
    assert entry is not None
    assert entry["version"] == "3.0.0"


def test_get_version_missing_returns_none(vfile):
    assert get_version(vfile, "nonexistent") is None


def test_remove_version_returns_true(vfile):
    set_version(vfile, "job-d", "1.0.0")
    assert remove_version(vfile, "job-d") is True


def test_remove_version_deletes_entry(vfile):
    set_version(vfile, "job-d", "1.0.0")
    remove_version(vfile, "job-d")
    assert get_version(vfile, "job-d") is None


def test_remove_version_missing_returns_false(vfile):
    assert remove_version(vfile, "ghost") is False


def test_all_versions_empty(vfile):
    assert all_versions(vfile) == {}


def test_all_versions_multiple_jobs(vfile):
    set_version(vfile, "job-x", "1.0")
    set_version(vfile, "job-y", "2.0")
    result = all_versions(vfile)
    assert set(result.keys()) == {"job-x", "job-y"}
