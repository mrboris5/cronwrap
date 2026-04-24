"""Tests for cronwrap.trend and cronwrap.trend_cli."""

from __future__ import annotations

import json
import os
import pytest

from cronwrap.trend import _slope, duration_trend, success_trend, trend_summary
from cronwrap.trend_cli import build_trend_parser, trend_main


# ---------------------------------------------------------------------------
# _slope
# ---------------------------------------------------------------------------

def test_slope_constant_series():
    assert _slope([5.0, 5.0, 5.0, 5.0]) == pytest.approx(0.0)


def test_slope_increasing():
    assert _slope([1.0, 2.0, 3.0, 4.0]) > 0


def test_slope_decreasing():
    assert _slope([4.0, 3.0, 2.0, 1.0]) < 0


def test_slope_single_value():
    assert _slope([42.0]) == 0.0


# ---------------------------------------------------------------------------
# duration_trend
# ---------------------------------------------------------------------------

def test_duration_trend_insufficient_data():
    assert duration_trend({"durations": [1.0, 2.0]}) is None


def test_duration_trend_stable():
    result = duration_trend({"durations": [2.0, 2.0, 2.0, 2.0, 2.0]})
    assert result == "stable"


def test_duration_trend_degrading():
    result = duration_trend({"durations": [1.0, 5.0, 9.0, 13.0, 17.0]})
    assert result == "degrading"


def test_duration_trend_improving():
    result = duration_trend({"durations": [17.0, 13.0, 9.0, 5.0, 1.0]})
    assert result == "improving"


# ---------------------------------------------------------------------------
# success_trend
# ---------------------------------------------------------------------------

def test_success_trend_insufficient_data():
    assert success_trend({"outcomes": [1, 0]}) is None


def test_success_trend_stable():
    result = success_trend({"outcomes": [1, 1, 1, 1, 1]})
    assert result == "stable"


def test_success_trend_degrading():
    result = success_trend({"outcomes": [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]})
    assert result == "degrading"


# ---------------------------------------------------------------------------
# trend_summary
# ---------------------------------------------------------------------------

def test_trend_summary(tmp_path):
    mf = tmp_path / "metrics.json"
    data = {
        "backup": {
            "durations": [2.0, 2.0, 2.0, 2.0, 2.0],
            "outcomes": [1, 1, 1, 1, 1],
        }
    }
    mf.write_text(json.dumps(data))
    summary = trend_summary("backup", str(mf))
    assert summary["job_id"] == "backup"
    assert summary["duration_trend"] == "stable"
    assert summary["success_trend"] == "stable"


def test_trend_summary_missing_job(tmp_path):
    mf = tmp_path / "metrics.json"
    mf.write_text(json.dumps({}))
    summary = trend_summary("ghost", str(mf))
    assert summary["duration_trend"] is None
    assert summary["success_trend"] is None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture
def mfile(tmp_path):
    path = tmp_path / "metrics.json"
    data = {
        "job_a": {
            "durations": [1.0, 1.0, 1.0, 1.0, 1.0],
            "outcomes": [1, 1, 1, 1, 1],
        },
        "job_b": {
            "durations": [],
            "outcomes": [],
        },
    }
    path.write_text(json.dumps(data))
    return str(path)


def _run(argv):
    return trend_main(argv)


def test_build_trend_parser_returns_parser():
    p = build_trend_parser()
    assert p is not None


def test_trend_main_all_jobs(mfile, capsys):
    rc = _run(["--metrics-file", mfile])
    assert rc == 0
    out = capsys.readouterr().out
    assert "job_a" in out
    assert "job_b" in out


def test_trend_main_single_job(mfile, capsys):
    rc = _run(["--metrics-file", mfile, "job_a"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "job_a" in out


def test_trend_main_unknown_job(mfile, capsys):
    rc = _run(["--metrics-file", mfile, "ghost"])
    assert rc == 1


def test_trend_main_no_metrics(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({}))
    rc = _run(["--metrics-file", str(empty)])
    assert rc == 1
