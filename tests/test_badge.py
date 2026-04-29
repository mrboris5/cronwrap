"""Tests for cronwrap.badge."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwrap.badge import build_badge, write_badge, badge_summary


@pytest.fixture()
def mfile(tmp_path: Path) -> str:
    data = {
        "job_a": {"success": 95, "failure": 5, "durations": []},
        "job_b": {"success": 70, "failure": 30, "durations": []},
        "job_c": {"success": 0, "failure": 10, "durations": []},
    }
    p = tmp_path / "metrics.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_build_badge_passing(mfile: str) -> None:
    badge = build_badge("job_a", mfile)
    assert badge["color"] == "brightgreen"
    assert "passing" in badge["message"]


def test_build_badge_degraded(mfile: str) -> None:
    badge = build_badge("job_b", mfile)
    assert badge["color"] == "yellow"
    assert "degraded" in badge["message"]


def test_build_badge_failing(mfile: str) -> None:
    badge = build_badge("job_c", mfile)
    assert badge["color"] == "red"
    assert "failing" in badge["message"]


def test_build_badge_unknown_job(mfile: str) -> None:
    badge = build_badge("nonexistent", mfile)
    assert badge["color"] == "lightgrey"
    assert "unknown" in badge["message"]
    assert "no data" in badge["message"]


def test_build_badge_schema_version(mfile: str) -> None:
    badge = build_badge("job_a", mfile)
    assert badge["schemaVersion"] == 1


def test_build_badge_label_is_job_id(mfile: str) -> None:
    badge = build_badge("job_a", mfile)
    assert badge["label"] == "job_a"


def test_write_badge_creates_file(mfile: str, tmp_path: Path) -> None:
    out = str(tmp_path / "badge.json")
    write_badge("job_a", mfile, out)
    assert Path(out).exists()
    data = json.loads(Path(out).read_text())
    assert data["label"] == "job_a"


def test_write_badge_valid_json(mfile: str, tmp_path: Path) -> None:
    out = str(tmp_path / "badge.json")
    write_badge("job_b", mfile, out)
    parsed = json.loads(Path(out).read_text())
    assert "message" in parsed


def test_badge_summary_returns_all_jobs(mfile: str) -> None:
    summaries = badge_summary(mfile)
    job_ids = [s["label"] for s in summaries]
    assert "job_a" in job_ids
    assert "job_b" in job_ids
    assert "job_c" in job_ids


def test_badge_summary_sorted(mfile: str) -> None:
    summaries = badge_summary(mfile)
    labels = [s["label"] for s in summaries]
    assert labels == sorted(labels)


def test_badge_missing_metrics_file(tmp_path: Path) -> None:
    missing = str(tmp_path / "no_such.json")
    badge = build_badge("any_job", missing)
    assert badge["color"] == "lightgrey"
