"""Tests for cronwrap.label."""
import json
import pytest
from pathlib import Path
from cronwrap.label import (
    load_labels, save_labels, add_label, remove_label,
    get_labels, jobs_with_label, clear_labels,
)


@pytest.fixture
def lfile(tmp_path):
    return str(tmp_path / "labels.json")


def test_load_labels_missing_file(lfile):
    assert load_labels(lfile) == {}


def test_load_labels_corrupt_file(lfile):
    Path(lfile).write_text("not-json")
    assert load_labels(lfile) == {}


def test_save_and_load_roundtrip(lfile):
    data = {"job1": ["critical", "prod"]}
    save_labels(data, lfile)
    assert load_labels(lfile) == data


def test_add_label_new_job(lfile):
    result = add_label("job1", "critical", lfile)
    assert "critical" in result


def test_add_label_no_duplicate(lfile):
    add_label("job1", "critical", lfile)
    result = add_label("job1", "critical", lfile)
    assert result.count("critical") == 1


def test_add_label_multiple(lfile):
    add_label("job1", "critical", lfile)
    result = add_label("job1", "prod", lfile)
    assert set(result) == {"critical", "prod"}


def test_remove_label(lfile):
    add_label("job1", "critical", lfile)
    add_label("job1", "prod", lfile)
    result = remove_label("job1", "critical", lfile)
    assert "critical" not in result
    assert "prod" in result


def test_remove_label_nonexistent(lfile):
    result = remove_label("job1", "ghost", lfile)
    assert result == []


def test_get_labels(lfile):
    add_label("job1", "nightly", lfile)
    assert "nightly" in get_labels("job1", lfile)


def test_get_labels_unknown_job(lfile):
    assert get_labels("unknown", lfile) == []


def test_jobs_with_label(lfile):
    add_label("job1", "critical", lfile)
    add_label("job2", "critical", lfile)
    add_label("job3", "normal", lfile)
    jobs = jobs_with_label("critical", lfile)
    assert set(jobs) == {"job1", "job2"}


def test_jobs_with_label_none(lfile):
    assert jobs_with_label("missing", lfile) == []


def test_clear_labels(lfile):
    add_label("job1", "critical", lfile)
    clear_labels("job1", lfile)
    assert get_labels("job1", lfile) == []


def test_clear_labels_unknown_job(lfile):
    clear_labels("ghost", lfile)  # should not raise
