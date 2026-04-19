"""Tests for cronwrap.checkpoint."""
import json
import os
import pytest

from cronwrap.checkpoint import (
    load_checkpoints,
    save_checkpoints,
    set_checkpoint,
    get_checkpoint,
    clear_checkpoint,
    clear_all_checkpoints,
)


@pytest.fixture
def cp_file(tmp_path):
    return str(tmp_path / "checkpoints.json")


def test_load_checkpoints_missing_file(cp_file):
    assert load_checkpoints(cp_file) == {}


def test_load_checkpoints_corrupt_file(cp_file):
    with open(cp_file, "w") as f:
        f.write("not json")
    assert load_checkpoints(cp_file) == {}


def test_save_and_load_roundtrip(cp_file):
    data = {"job1": "page_42", "job2": 100}
    save_checkpoints(cp_file, data)
    assert load_checkpoints(cp_file) == data


def test_set_checkpoint_creates_entry(cp_file):
    set_checkpoint(cp_file, "job1", "offset_10")
    assert get_checkpoint(cp_file, "job1") == "offset_10"


def test_set_checkpoint_overwrites(cp_file):
    set_checkpoint(cp_file, "job1", "v1")
    set_checkpoint(cp_file, "job1", "v2")
    assert get_checkpoint(cp_file, "job1") == "v2"


def test_get_checkpoint_default(cp_file):
    assert get_checkpoint(cp_file, "missing") is None
    assert get_checkpoint(cp_file, "missing", default=0) == 0


def test_clear_checkpoint_existing(cp_file):
    set_checkpoint(cp_file, "job1", "x")
    result = clear_checkpoint(cp_file, "job1")
    assert result is True
    assert get_checkpoint(cp_file, "job1") is None


def test_clear_checkpoint_nonexistent(cp_file):
    result = clear_checkpoint(cp_file, "ghost")
    assert result is False


def test_clear_all_checkpoints(cp_file):
    set_checkpoint(cp_file, "a", 1)
    set_checkpoint(cp_file, "b", 2)
    count = clear_all_checkpoints(cp_file)
    assert count == 2
    assert load_checkpoints(cp_file) == {}


def test_multiple_jobs_independent(cp_file):
    set_checkpoint(cp_file, "job1", "step_1")
    set_checkpoint(cp_file, "job2", "step_5")
    assert get_checkpoint(cp_file, "job1") == "step_1"
    assert get_checkpoint(cp_file, "job2") == "step_5"
