"""Tests for cronwrap.sla module."""

import json
import pytest
from pathlib import Path
from cronwrap.sla import (
    load_sla_records, save_sla_records, record_sla_run,
    sla_compliance, sla_summary,
)


@pytest.fixture
def sla_file(tmp_path):
    return str(tmp_path / "sla.json")


def test_load_sla_records_missing_file(sla_file):
    assert load_sla_records(sla_file) == {}


def test_load_sla_records_corrupt_file(sla_file):
    Path(sla_file).write_text("not json")
    assert load_sla_records(sla_file) == {}


def test_save_and_load_roundtrip(sla_file):
    data = {"job1": {"total": 1, "violations": 0, "history": []}}
    save_sla_records(sla_file, data)
    loaded = load_sla_records(sla_file)
    assert loaded["job1"]["total"] == 1


def test_record_sla_run_creates_entry(sla_file):
    run = record_sla_run(sla_file, "job1", duration=1.5, success=True)
    assert run["success"] is True
    assert run["duration"] == 1.5
    assert run["breached"] is False


def test_record_sla_run_detects_breach(sla_file):
    run = record_sla_run(sla_file, "job1", duration=10.0, success=True, budget_seconds=5.0)
    assert run["breached"] is True


def test_record_sla_run_no_breach_within_budget(sla_file):
    run = record_sla_run(sla_file, "job1", duration=3.0, success=True, budget_seconds=5.0)
    assert run["breached"] is False


def test_record_sla_run_increments_total(sla_file):
    record_sla_run(sla_file, "job1", duration=1.0, success=True)
    record_sla_run(sla_file, "job1", duration=1.0, success=True)
    records = load_sla_records(sla_file)
    assert records["job1"]["total"] == 2


def test_record_sla_run_counts_violations_on_failure(sla_file):
    record_sla_run(sla_file, "job1", duration=1.0, success=False)
    records = load_sla_records(sla_file)
    assert records["job1"]["violations"] == 1


def test_record_sla_run_counts_violations_on_breach(sla_file):
    record_sla_run(sla_file, "job1", duration=10.0, success=True, budget_seconds=5.0)
    records = load_sla_records(sla_file)
    assert records["job1"]["violations"] == 1


def test_sla_compliance_no_runs(sla_file):
    assert sla_compliance(sla_file, "unknown") == 1.0


def test_sla_compliance_all_ok(sla_file):
    record_sla_run(sla_file, "job1", duration=1.0, success=True)
    record_sla_run(sla_file, "job1", duration=1.0, success=True)
    assert sla_compliance(sla_file, "job1") == 1.0


def test_sla_compliance_partial(sla_file):
    record_sla_run(sla_file, "job1", duration=1.0, success=True)
    record_sla_run(sla_file, "job1", duration=1.0, success=False)
    compliance = sla_compliance(sla_file, "job1")
    assert compliance == 0.5


def test_sla_summary_structure(sla_file):
    record_sla_run(sla_file, "job1", duration=2.0, success=True)
    summary = sla_summary(sla_file, "job1")
    assert summary["job_id"] == "job1"
    assert summary["total"] == 1
    assert summary["violations"] == 0
    assert summary["compliance"] == 1.0
    assert summary["last_run"] is not None


def test_save_trims_history(sla_file):
    records = {
        "job1": {
            "total": 600,
            "violations": 0,
            "history": [{"timestamp": "t", "duration": 1.0, "success": True, "breached": False}] * 600,
        }
    }
    save_sla_records(sla_file, records, max_entries=500)
    loaded = load_sla_records(sla_file)
    assert len(loaded["job1"]["history"]) == 500
