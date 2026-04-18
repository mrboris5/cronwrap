"""Tests for cronwrap.lock module."""

import os
import pytest
from pathlib import Path
from cronwrap.lock import JobLock, LockError


@pytest.fixture
def lock_dir(tmp_path):
    return str(tmp_path / "locks")


def test_acquire_creates_lock_file(lock_dir):
    lock = JobLock(lock_dir, "myjob")
    lock.acquire()
    assert lock.is_locked
    lock.release()


def test_release_removes_lock_file(lock_dir):
    lock = JobLock(lock_dir, "myjob")
    lock.acquire()
    lock.release()
    assert not lock.is_locked


def test_context_manager(lock_dir):
    lock = JobLock(lock_dir, "myjob")
    with lock:
        assert lock.is_locked
    assert not lock.is_locked


def test_lock_file_contains_pid(lock_dir):
    lock = JobLock(lock_dir, "myjob")
    lock.acquire()
    content = Path(lock.lock_file).read_text()
    assert content == str(os.getpid())
    lock.release()


def test_second_acquire_raises_immediately(lock_dir):
    lock1 = JobLock(lock_dir, "myjob", timeout=0)
    lock2 = JobLock(lock_dir, "myjob", timeout=0)
    lock1.acquire()
    with pytest.raises(LockError):
        lock2.acquire()
    lock1.release()


def test_lock_dir_created_if_missing(tmp_path):
    lock_dir = str(tmp_path / "nested" / "locks")
    lock = JobLock(lock_dir, "myjob")
    lock.acquire()
    assert Path(lock_dir).exists()
    lock.release()


def test_release_without_acquire_is_safe(lock_dir):
    lock = JobLock(lock_dir, "myjob")
    lock.release()  # should not raise


def test_different_jobs_do_not_conflict(lock_dir):
    lock1 = JobLock(lock_dir, "job_a")
    lock2 = JobLock(lock_dir, "job_b")
    lock1.acquire()
    lock2.acquire()  # should not raise
    lock1.release()
    lock2.release()
