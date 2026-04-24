"""Tests for cronwrap.baseline."""

import pytest

from cronwrap.baseline import (
    check_baseline,
    get_baseline,
    load_baselines,
    remove_baseline,
    save_baselines,
    set_baseline,
)


@pytest.fixture
def bfile(tmp_path):
    return str(tmp_path / "baselines.json")


def test_load_baselines_missing_file(bfile):
    assert load_baselines(bfile) == {}


def test_load_baselines_corrupt_file(bfile):
    with open(bfile, "w") as fh:
        fh.write("not json{{{")
    assert load_baselines(bfile) == {}


def test_save_and_load_roundtrip(bfile):
    data = {"job1": {"expected_seconds": 30.0}}
    save_baselines(data, bfile)
    assert load_baselines(bfile) == data


def test_set_baseline_creates_entry(bfile):
    entry = set_baseline("backup", 120.0, path=bfile)
    assert entry["expected_seconds"] == 120.0
    assert get_baseline("backup", path=bfile) == 120.0


def test_set_baseline_updates_existing(bfile):
    set_baseline("backup", 60.0, path=bfile)
    set_baseline("backup", 90.0, path=bfile)
    assert get_baseline("backup", path=bfile) == 90.0


def test_set_baseline_invalid_seconds(bfile):
    with pytest.raises(ValueError):
        set_baseline("job", 0, path=bfile)
    with pytest.raises(ValueError):
        set_baseline("job", -5.0, path=bfile)


def test_get_baseline_missing_job(bfile):
    assert get_baseline("nonexistent", path=bfile) is None


def test_remove_baseline_existing(bfile):
    set_baseline("job1", 10.0, path=bfile)
    assert remove_baseline("job1", path=bfile) is True
    assert get_baseline("job1", path=bfile) is None


def test_remove_baseline_not_found(bfile):
    assert remove_baseline("ghost", path=bfile) is False


def test_check_baseline_no_baseline(bfile):
    assert check_baseline("job", 999.0, path=bfile) is None


def test_check_baseline_within_margin(bfile):
    set_baseline("job", 100.0, path=bfile)
    # 124s is 24% over 100s — within default 25% margin
    assert check_baseline("job", 124.0, path=bfile) is None


def test_check_baseline_exceeds_margin(bfile):
    set_baseline("job", 100.0, path=bfile)
    warning = check_baseline("job", 130.0, path=bfile)
    assert warning is not None
    assert "130" in warning or "130.0" in warning
    assert "job" in warning


def test_check_baseline_custom_margin(bfile):
    set_baseline("job", 100.0, path=bfile)
    # 5% margin — 106s should trigger
    warning = check_baseline("job", 106.0, margin=0.05, path=bfile)
    assert warning is not None
