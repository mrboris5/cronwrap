"""Tests for cronwrap.tag_index."""

import pytest
from pathlib import Path
from cronwrap.tag_index import (
    load_index,
    save_index,
    index_job,
    deindex_job,
    jobs_for_tag,
    tags_for_job,
    all_tags,
)


@pytest.fixture
def idx_file(tmp_path) -> Path:
    return tmp_path / "tag_index.json"


def test_load_index_missing_file(idx_file):
    assert load_index(idx_file) == {}


def test_load_index_corrupt_file(idx_file):
    idx_file.write_text("not-json")
    assert load_index(idx_file) == {}


def test_save_and_load_roundtrip(idx_file):
    data = {"env:prod": ["job-a", "job-b"], "team:ops": ["job-a"]}
    save_index(data, idx_file)
    assert load_index(idx_file) == data


def test_index_job_creates_entry(idx_file):
    index_job("job-1", ["env:dev", "team:eng"], idx_file)
    assert "job-1" in jobs_for_tag("env:dev", idx_file)
    assert "job-1" in jobs_for_tag("team:eng", idx_file)


def test_index_job_replaces_old_tags(idx_file):
    index_job("job-1", ["env:dev"], idx_file)
    index_job("job-1", ["env:prod"], idx_file)
    assert "job-1" not in jobs_for_tag("env:dev", idx_file)
    assert "job-1" in jobs_for_tag("env:prod", idx_file)


def test_index_job_no_duplicates(idx_file):
    index_job("job-1", ["env:dev"], idx_file)
    index_job("job-1", ["env:dev"], idx_file)
    assert jobs_for_tag("env:dev", idx_file).count("job-1") == 1


def test_deindex_job_removes_from_all_tags(idx_file):
    index_job("job-1", ["env:dev", "team:eng"], idx_file)
    deindex_job("job-1", idx_file)
    assert jobs_for_tag("env:dev", idx_file) == []
    assert jobs_for_tag("team:eng", idx_file) == []


def test_deindex_job_prunes_empty_tags(idx_file):
    index_job("job-1", ["env:dev"], idx_file)
    deindex_job("job-1", idx_file)
    assert "env:dev" not in all_tags(idx_file)


def test_jobs_for_tag_unknown_tag(idx_file):
    assert jobs_for_tag("no-such-tag", idx_file) == []


def test_jobs_for_tag_sorted(idx_file):
    index_job("job-z", ["shared"], idx_file)
    index_job("job-a", ["shared"], idx_file)
    assert jobs_for_tag("shared", idx_file) == ["job-a", "job-z"]


def test_tags_for_job(idx_file):
    index_job("job-1", ["env:prod", "team:ops"], idx_file)
    result = tags_for_job("job-1", idx_file)
    assert result == ["env:prod", "team:ops"]


def test_tags_for_job_unknown(idx_file):
    assert tags_for_job("ghost", idx_file) == []


def test_all_tags_sorted(idx_file):
    index_job("job-1", ["z-tag", "a-tag"], idx_file)
    assert all_tags(idx_file) == ["a-tag", "z-tag"]


def test_all_tags_empty(idx_file):
    assert all_tags(idx_file) == []
