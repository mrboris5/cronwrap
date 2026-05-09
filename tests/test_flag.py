"""Tests for cronwrap/flag.py"""

import pytest
from cronwrap.flag import (
    load_flags,
    save_flags,
    set_flag,
    get_flag,
    remove_flag,
    is_enabled,
    all_flags,
    flag_summary,
)


@pytest.fixture
def ffile(tmp_path):
    return str(tmp_path / "flags.json")


def test_load_flags_missing_file(ffile):
    assert load_flags(ffile) == {}


def test_load_flags_corrupt_file(tmp_path):
    p = tmp_path / "flags.json"
    p.write_text("not json")
    assert load_flags(str(p)) == {}


def test_save_and_load_roundtrip(ffile):
    data = {"my_feature": True, "max_retries": 3}
    save_flags(data, ffile)
    assert load_flags(ffile) == data


def test_set_flag_creates_entry(ffile):
    result = set_flag("dark_mode", True, ffile)
    assert result["dark_mode"] is True


def test_set_flag_overwrites_existing(ffile):
    set_flag("limit", 5, ffile)
    set_flag("limit", 10, ffile)
    assert get_flag("limit", path=ffile) == 10


def test_get_flag_returns_default_when_missing(ffile):
    assert get_flag("nonexistent", default="fallback", path=ffile) == "fallback"


def test_get_flag_returns_value(ffile):
    set_flag("feature_x", "enabled", ffile)
    assert get_flag("feature_x", path=ffile) == "enabled"


def test_remove_flag_existing(ffile):
    set_flag("to_remove", True, ffile)
    assert remove_flag("to_remove", ffile) is True
    assert get_flag("to_remove", path=ffile) is None


def test_remove_flag_nonexistent(ffile):
    assert remove_flag("ghost", ffile) is False


def test_is_enabled_true(ffile):
    set_flag("beta", True, ffile)
    assert is_enabled("beta", ffile) is True


def test_is_enabled_false_value(ffile):
    set_flag("beta", False, ffile)
    assert is_enabled("beta", ffile) is False


def test_is_enabled_missing(ffile):
    assert is_enabled("missing", ffile) is False


def test_all_flags_returns_dict(ffile):
    set_flag("a", 1, ffile)
    set_flag("b", 2, ffile)
    flags = all_flags(ffile)
    assert flags == {"a": 1, "b": 2}


def test_flag_summary_no_flags(ffile):
    summary = flag_summary(ffile)
    assert "No feature flags" in summary


def test_flag_summary_with_flags(ffile):
    set_flag("alpha", True, ffile)
    summary = flag_summary(ffile)
    assert "alpha" in summary
    assert "True" in summary
