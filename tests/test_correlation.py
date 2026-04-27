"""Tests for cronwrap.correlation."""
import json
from pathlib import Path

import pytest

from cronwrap.correlation import (
    all_correlation_ids,
    get_correlated_runs,
    new_correlation_id,
    record_correlation,
    remove_correlation,
)

TS = "2024-01-15T10:00:00"


@pytest.fixture()
def cfile(tmp_path: Path) -> Path:
    return tmp_path / "correlations.json"


def test_new_correlation_id_is_string():
    cid = new_correlation_id()
    assert isinstance(cid, str)
    assert len(cid) == 36  # UUID4 format


def test_new_correlation_ids_are_unique():
    assert new_correlation_id() != new_correlation_id()


def test_record_correlation_creates_entry(cfile: Path):
    entry = record_correlation("cid-1", "backup", "success", TS, path=cfile)
    assert entry["job_id"] == "backup"
    assert entry["status"] == "success"
    assert entry["timestamp"] == TS


def test_record_correlation_persists(cfile: Path):
    record_correlation("cid-1", "backup", "success", TS, path=cfile)
    runs = get_correlated_runs("cid-1", path=cfile)
    assert len(runs) == 1
    assert runs[0]["job_id"] == "backup"


def test_record_multiple_jobs_under_same_id(cfile: Path):
    record_correlation("cid-1", "job-a", "success", TS, path=cfile)
    record_correlation("cid-1", "job-b", "failure", TS, path=cfile)
    runs = get_correlated_runs("cid-1", path=cfile)
    assert len(runs) == 2
    job_ids = {r["job_id"] for r in runs}
    assert job_ids == {"job-a", "job-b"}


def test_record_correlation_with_extra(cfile: Path):
    entry = record_correlation(
        "cid-1", "etl", "success", TS, path=cfile, extra={"rows": 42}
    )
    assert entry["rows"] == 42
    runs = get_correlated_runs("cid-1", path=cfile)
    assert runs[0]["rows"] == 42


def test_get_correlated_runs_missing_file(cfile: Path):
    assert get_correlated_runs("no-such-id", path=cfile) == []


def test_get_correlated_runs_unknown_id(cfile: Path):
    record_correlation("cid-1", "job", "success", TS, path=cfile)
    assert get_correlated_runs("cid-x", path=cfile) == []


def test_all_correlation_ids(cfile: Path):
    record_correlation("cid-1", "job-a", "success", TS, path=cfile)
    record_correlation("cid-2", "job-b", "failure", TS, path=cfile)
    ids = all_correlation_ids(path=cfile)
    assert set(ids) == {"cid-1", "cid-2"}


def test_all_correlation_ids_missing_file(cfile: Path):
    assert all_correlation_ids(path=cfile) == []


def test_remove_correlation_returns_true(cfile: Path):
    record_correlation("cid-1", "job", "success", TS, path=cfile)
    assert remove_correlation("cid-1", path=cfile) is True


def test_remove_correlation_deletes_entry(cfile: Path):
    record_correlation("cid-1", "job", "success", TS, path=cfile)
    remove_correlation("cid-1", path=cfile)
    assert get_correlated_runs("cid-1", path=cfile) == []


def test_remove_correlation_missing_returns_false(cfile: Path):
    assert remove_correlation("no-such", path=cfile) is False


def test_corrupt_file_returns_empty(cfile: Path):
    cfile.write_text("not valid json")
    assert get_correlated_runs("cid-1", path=cfile) == []
