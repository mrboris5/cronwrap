"""Tests for cronwrap.precondition."""
import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from cronwrap.precondition import check_preconditions, PreconditionResult


@pytest.fixture
def tmp_files(tmp_path):
    return tmp_path


def _iso(dt):
    return dt.isoformat()


def now():
    return datetime.now(timezone.utc)


def test_no_checks_returns_allowed():
    result = check_preconditions("job1")
    assert result.allowed is True
    assert result.summary() == "OK"


def test_unmet_dependency_blocks(tmp_files):
    hist = str(tmp_files / "hist.json")
    Path(hist).write_text(json.dumps([]))
    result = check_preconditions("job1", history_file=hist, dep_job_ids=["dep1"])
    assert result.allowed is False
    assert "dep1" in result.summary()


def test_met_dependency_allows(tmp_files):
    hist = str(tmp_files / "hist.json")
    Path(hist).write_text(json.dumps([
        {"job_id": "dep1", "exit_code": 0, "timestamp": _iso(now())}
    ]))
    result = check_preconditions("job1", history_file=hist, dep_job_ids=["dep1"])
    assert result.allowed is True


def test_open_circuit_blocks(tmp_files):
    state_file = str(tmp_files / "circuit.json")
    state = {"job1": {"failures": 5, "last_failure": _iso(now()), "open": True}}
    Path(state_file).write_text(json.dumps(state))
    result = check_preconditions(
        "job1",
        circuit_state_file=state_file,
        circuit_threshold=3,
        circuit_reset_seconds=300,
    )
    assert result.allowed is False
    assert "Circuit" in result.summary()


def test_throttle_blocks(tmp_files):
    recent = _iso(now() - timedelta(seconds=10))
    result = check_preconditions(
        "job1",
        last_run_timestamp=recent,
        min_interval="60s",
    )
    assert result.allowed is False


def test_throttle_allows_after_interval(tmp_files):
    old = _iso(now() - timedelta(seconds=120))
    result = check_preconditions(
        "job1",
        last_run_timestamp=old,
        min_interval="60s",
    )
    assert result.allowed is True


def test_multiple_failures_combined(tmp_files):
    hist = str(tmp_files / "hist.json")
    Path(hist).write_text(json.dumps([]))
    recent = _iso(now() - timedelta(seconds=5))
    result = check_preconditions(
        "job1",
        history_file=hist,
        dep_job_ids=["dep1"],
        last_run_timestamp=recent,
        min_interval="60s",
    )
    assert result.allowed is False
    assert len(result.reasons) == 2


def test_summary_ok():
    r = PreconditionResult(allowed=True)
    assert r.summary() == "OK"


def test_summary_reasons():
    r = PreconditionResult(allowed=False, reasons=["reason A", "reason B"])
    assert "reason A" in r.summary()
    assert "reason B" in r.summary()
