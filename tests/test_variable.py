"""Tests for cronwrap.variable."""
from __future__ import annotations

import json
import pytest

from cronwrap.variable import (
    clear_variables,
    get_all_variables,
    get_variable,
    load_variables,
    remove_variable,
    set_variable,
)


@pytest.fixture()
def vfile(tmp_path):
    return str(tmp_path / "variables.json")


def test_load_variables_missing_file(vfile):
    assert load_variables(vfile) == {}


def test_load_variables_corrupt_file(vfile, tmp_path):
    (tmp_path / "variables.json").write_text("not-json")
    assert load_variables(vfile) == {}


def test_save_and_load_roundtrip(vfile):
    set_variable(vfile, "job1", "retries", 3)
    assert load_variables(vfile)["job1"]["retries"] == 3


def test_set_variable_creates_entry(vfile):
    result = set_variable(vfile, "job1", "env", "production")
    assert result["env"] == "production"


def test_set_variable_overwrites_existing(vfile):
    set_variable(vfile, "job1", "mode", "fast")
    set_variable(vfile, "job1", "mode", "slow")
    assert get_variable(vfile, "job1", "mode") == "slow"


def test_set_variable_multiple_keys(vfile):
    set_variable(vfile, "job1", "a", 1)
    set_variable(vfile, "job1", "b", 2)
    all_vars = get_all_variables(vfile, "job1")
    assert all_vars == {"a": 1, "b": 2}


def test_get_variable_missing_job(vfile):
    assert get_variable(vfile, "ghost", "key") is None


def test_get_variable_missing_key(vfile):
    set_variable(vfile, "job1", "x", 42)
    assert get_variable(vfile, "job1", "y") is None


def test_get_all_variables_empty(vfile):
    assert get_all_variables(vfile, "job1") == {}


def test_remove_variable_returns_true(vfile):
    set_variable(vfile, "job1", "k", "v")
    assert remove_variable(vfile, "job1", "k") is True


def test_remove_variable_deletes_key(vfile):
    set_variable(vfile, "job1", "k", "v")
    remove_variable(vfile, "job1", "k")
    assert get_variable(vfile, "job1", "k") is None


def test_remove_variable_missing_returns_false(vfile):
    assert remove_variable(vfile, "job1", "nope") is False


def test_remove_last_variable_cleans_job_entry(vfile):
    set_variable(vfile, "job1", "only", 1)
    remove_variable(vfile, "job1", "only")
    data = load_variables(vfile)
    assert "job1" not in data


def test_clear_variables_returns_count(vfile):
    set_variable(vfile, "job1", "a", 1)
    set_variable(vfile, "job1", "b", 2)
    assert clear_variables(vfile, "job1") == 2


def test_clear_variables_removes_all(vfile):
    set_variable(vfile, "job1", "x", 10)
    clear_variables(vfile, "job1")
    assert get_all_variables(vfile, "job1") == {}


def test_clear_variables_missing_job_returns_zero(vfile):
    assert clear_variables(vfile, "ghost") == 0


def test_multiple_jobs_isolated(vfile):
    set_variable(vfile, "job1", "shared", "alpha")
    set_variable(vfile, "job2", "shared", "beta")
    assert get_variable(vfile, "job1", "shared") == "alpha"
    assert get_variable(vfile, "job2", "shared") == "beta"
