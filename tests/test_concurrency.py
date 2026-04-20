"""Tests for cronwrap.concurrency."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cronwrap.concurrency import (
    concurrency_reason,
    is_concurrency_limited,
    load_active,
    prune_dead,
    register_pid,
    save_active,
    unregister_pid,
)


@pytest.fixture()
def sf(tmp_path: Path) -> str:
    return str(tmp_path / "concurrency.json")


def test_load_active_missing_file(sf: str) -> None:
    assert load_active(sf) == []


def test_load_active_corrupt_file(sf: str) -> None:
    Path(sf).write_text("not-json")
    assert load_active(sf) == []


def test_save_and_load_roundtrip(sf: str) -> None:
    save_active(sf, [1, 2, 3])
    assert load_active(sf) == [1, 2, 3]


def test_prune_dead_keeps_self() -> None:
    pid = os.getpid()
    result = prune_dead([pid])
    assert pid in result


def test_prune_dead_removes_nonexistent() -> None:
    # PID 0 is never a valid user process
    dead_pid = 99999999
    result = prune_dead([dead_pid])
    assert dead_pid not in result


def test_is_concurrency_limited_zero_max(sf: str) -> None:
    """max_concurrent=0 means no limit."""
    assert is_concurrency_limited(sf, 0) is False


def test_is_concurrency_limited_below_max(sf: str) -> None:
    save_active(sf, [os.getpid()])
    assert is_concurrency_limited(sf, 5) is False


def test_is_concurrency_limited_at_max(sf: str) -> None:
    save_active(sf, [os.getpid()])
    assert is_concurrency_limited(sf, 1) is True


def test_register_pid_adds_current(sf: str) -> None:
    register_pid(sf)
    assert os.getpid() in load_active(sf)


def test_register_pid_no_duplicate(sf: str) -> None:
    register_pid(sf)
    register_pid(sf)
    pids = load_active(sf)
    assert pids.count(os.getpid()) == 1


def test_unregister_pid_removes_current(sf: str) -> None:
    register_pid(sf)
    unregister_pid(sf)
    assert os.getpid() not in load_active(sf)


def test_unregister_pid_missing_file(sf: str) -> None:
    """Unregistering when no file exists should not raise."""
    unregister_pid(sf)  # must not raise


def test_concurrency_reason_contains_counts(sf: str) -> None:
    save_active(sf, [os.getpid()])
    reason = concurrency_reason(sf, 3)
    assert "1/3" in reason
    assert str(os.getpid()) in reason
