"""Tests for cronwrap.manifest."""
import json
import pytest
from cronwrap.manifest import (
    load_manifest,
    save_manifest,
    register_job,
    get_job,
    remove_job,
    list_jobs,
)


@pytest.fixture()
def mfile(tmp_path):
    return str(tmp_path / "manifest.json")


def test_load_manifest_missing_file(mfile):
    assert load_manifest(mfile) == {}


def test_load_manifest_corrupt_file(mfile, tmp_path):
    (tmp_path / "manifest.json").write_text("not json")
    assert load_manifest(mfile) == {}


def test_save_and_load_roundtrip(mfile):
    data = {"job1": {"job_id": "job1", "command": "echo hi"}}
    save_manifest(mfile, data)
    assert load_manifest(mfile) == data


def test_register_job_creates_entry(mfile):
    entry = register_job(mfile, "backup", "rsync -a /src /dst")
    assert entry["job_id"] == "backup"
    assert entry["command"] == "rsync -a /src /dst"


def test_register_job_persists(mfile):
    register_job(mfile, "cleanup", "rm -rf /tmp/old")
    manifest = load_manifest(mfile)
    assert "cleanup" in manifest


def test_register_job_with_tags(mfile):
    entry = register_job(mfile, "report", "./gen_report.sh", tags=["daily", "finance"])
    assert entry["tags"] == ["daily", "finance"]


def test_register_job_updates_existing(mfile):
    register_job(mfile, "myjob", "old_cmd")
    register_job(mfile, "myjob", "new_cmd", description="updated")
    entry = get_job(mfile, "myjob")
    assert entry["command"] == "new_cmd"
    assert entry["description"] == "updated"


def test_get_job_returns_entry(mfile):
    register_job(mfile, "j1", "echo 1")
    entry = get_job(mfile, "j1")
    assert entry is not None
    assert entry["command"] == "echo 1"


def test_get_job_missing_returns_none(mfile):
    assert get_job(mfile, "nonexistent") is None


def test_remove_job_returns_true(mfile):
    register_job(mfile, "to_remove", "cmd")
    assert remove_job(mfile, "to_remove") is True


def test_remove_job_actually_removes(mfile):
    register_job(mfile, "gone", "cmd")
    remove_job(mfile, "gone")
    assert get_job(mfile, "gone") is None


def test_remove_job_missing_returns_false(mfile):
    assert remove_job(mfile, "ghost") is False


def test_list_jobs_sorted(mfile):
    register_job(mfile, "zzz", "c")
    register_job(mfile, "aaa", "a")
    register_job(mfile, "mmm", "b")
    ids = [e["job_id"] for e in list_jobs(mfile)]
    assert ids == ["aaa", "mmm", "zzz"]


def test_list_jobs_empty(mfile):
    assert list_jobs(mfile) == []
