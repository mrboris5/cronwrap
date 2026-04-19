import json
import pytest
from cronwrap.circuit import (
    load_state,
    save_state,
    is_open,
    record_success,
    record_failure,
    open_reason,
    DEFAULT_THRESHOLD,
)


@pytest.fixture
def state_file(tmp_path):
    return str(tmp_path / "circuit.json")


def test_load_state_missing_file(state_file):
    state = load_state(state_file)
    assert state == {"failures": 0, "open": False}


def test_load_state_corrupt_file(state_file):
    open(state_file, "w").write("not-json")
    state = load_state(state_file)
    assert state == {"failures": 0, "open": False}


def test_save_and_load_roundtrip(state_file):
    save_state(state_file, {"failures": 2, "open": False})
    state = load_state(state_file)
    assert state["failures"] == 2
    assert state["open"] is False


def test_is_open_false_initially(state_file):
    assert is_open(state_file) is False


def test_is_open_after_threshold(state_file):
    for _ in range(DEFAULT_THRESHOLD):
        record_failure(state_file)
    assert is_open(state_file) is True


def test_record_success_resets(state_file):
    record_failure(state_file)
    record_failure(state_file)
    state = record_success(state_file)
    assert state["failures"] == 0
    assert state["open"] is False
    assert is_open(state_file) is False


def test_record_failure_increments(state_file):
    state = record_failure(state_file)
    assert state["failures"] == 1
    assert state["open"] is False


def test_record_failure_opens_circuit_at_threshold(state_file):
    for _ in range(DEFAULT_THRESHOLD - 1):
        record_failure(state_file)
    state = record_failure(state_file)
    assert state["open"] is True


def test_custom_threshold(state_file):
    record_failure(state_file)
    assert is_open(state_file, threshold=1) is True
    assert is_open(state_file, threshold=5) is False


def test_open_reason_contains_threshold(state_file):
    record_failure(state_file)
    reason = open_reason(state_file, threshold=DEFAULT_THRESHOLD)
    assert str(DEFAULT_THRESHOLD) in reason
    assert "failure" in reason
