"""Tests for cronwrap.env module."""
import os
import pytest
from cronwrap.env import (
    EnvError,
    require_vars,
    load_env_file,
    inject_env,
    apply_env_file,
    get_with_default,
)


def test_require_vars_all_present(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    monkeypatch.setenv("BAZ", "qux")
    require_vars(["FOO", "BAZ"])  # should not raise


def test_require_vars_missing_raises(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    with pytest.raises(EnvError, match="MISSING_VAR"):
        require_vars(["MISSING_VAR"])


def test_require_vars_partial_missing(monkeypatch):
    monkeypatch.setenv("PRESENT", "yes")
    monkeypatch.delenv("ABSENT", raising=False)
    with pytest.raises(EnvError, match="ABSENT"):
        require_vars(["PRESENT", "ABSENT"])


def test_load_env_file_basic(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=value1\nKEY2=value2\n")
    result = load_env_file(str(env_file))
    assert result == {"KEY1": "value1", "KEY2": "value2"}


def test_load_env_file_ignores_comments_and_blanks(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\n\nKEY=val\n")
    result = load_env_file(str(env_file))
    assert result == {"KEY": "val"}


def test_load_env_file_strips_quotes(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('KEY="quoted value"\n')
    result = load_env_file(str(env_file))
    assert result["KEY"] == "quoted value"


def test_load_env_file_invalid_line(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BADLINE\n")
    with pytest.raises(EnvError, match="Invalid env file line"):
        load_env_file(str(env_file))


def test_inject_env_sets_vars(monkeypatch):
    monkeypatch.delenv("INJECT_TEST", raising=False)
    inject_env({"INJECT_TEST": "hello"})
    assert os.environ["INJECT_TEST"] == "hello"


def test_inject_env_no_override(monkeypatch):
    monkeypatch.setenv("EXISTING", "original")
    inject_env({"EXISTING": "new"}, override=False)
    assert os.environ["EXISTING"] == "original"


def test_inject_env_with_override(monkeypatch):
    monkeypatch.setenv("EXISTING", "original")
    inject_env({"EXISTING": "new"}, override=True)
    assert os.environ["EXISTING"] == "new"


def test_apply_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("APPLY_KEY=apply_val\n")
    monkeypatch.delenv("APPLY_KEY", raising=False)
    pairs = apply_env_file(str(env_file))
    assert pairs == {"APPLY_KEY": "apply_val"}
    assert os.environ["APPLY_KEY"] == "apply_val"


def test_get_with_default_present(monkeypatch):
    monkeypatch.setenv("MY_VAR", "myval")
    assert get_with_default("MY_VAR", "default") == "myval"


def test_get_with_default_missing(monkeypatch):
    monkeypatch.delenv("MY_VAR", raising=False)
    assert get_with_default("MY_VAR", "fallback") == "fallback"
