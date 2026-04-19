"""Tests for cronwrap.escalation."""

import pytest
from cronwrap.escalation import (
    load_state,
    save_state,
    record_failure,
    record_success,
    should_escalate,
    escalation_reason,
)


@pytest.fixture
def esc_file(tmp_path):
    return str(tmp_path / "escalation.json")


def test_load_state_missing_file(esc_file):
    assert load_state(esc_file) == {}


def test_load_state_corrupt_file(esc_file):
    with open(esc_file, "w") as f:
        f.write("not json")
    assert load_state(esc_file) == {}


def test_save_and_load_roundtrip(esc_file):
    save_state(esc_file, {"job1": {"consecutive_failures": 2}})
    state = load_state(esc_file)
    assert state["job1"]["consecutive_failures"] == 2


def test_record_failure_increments(esc_file):
    count = record_failure(esc_file, "job1")
    assert count == 1
    count = record_failure(esc_file, "job1")
    assert count == 2


def test_record_failure_independent_jobs(esc_file):
    record_failure(esc_file, "job1")
    record_failure(esc_file, "job1")
    record_failure(esc_file, "job2")
    state = load_state(esc_file)
    assert state["job1"]["consecutive_failures"] == 2
    assert state["job2"]["consecutive_failures"] == 1


def test_record_success_resets_count(esc_file):
    record_failure(esc_file, "job1")
    record_failure(esc_file, "job1")
    record_success(esc_file, "job1")
    state = load_state(esc_file)
    assert state["job1"]["consecutive_failures"] == 0


def test_record_success_no_prior_state(esc_file):
    # Should not raise even if job never recorded
    record_success(esc_file, "nonexistent")


def test_should_escalate_below_threshold(esc_file):
    record_failure(esc_file, "job1")
    record_failure(esc_file, "job1")
    assert not should_escalate(esc_file, "job1", threshold=3)


def test_should_escalate_at_threshold(esc_file):
    for _ in range(3):
        record_failure(esc_file, "job1")
    assert should_escalate(esc_file, "job1", threshold=3)


def test_should_escalate_above_threshold(esc_file):
    for _ in range(5):
        record_failure(esc_file, "job1")
    assert should_escalate(esc_file, "job1", threshold=3)


def test_should_escalate_no_state(esc_file):
    assert not should_escalate(esc_file, "job1")


def test_escalation_reason_contains_job_id(esc_file):
    record_failure(esc_file, "myjob")
    reason = escalation_reason(esc_file, "myjob", threshold=3)
    assert "myjob" in reason
    assert "1" in reason
    assert "3" in reason
