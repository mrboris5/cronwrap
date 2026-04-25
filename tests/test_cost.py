"""Tests for cronwrap.cost and cronwrap.cost_cli."""

from __future__ import annotations

import json
import pytest

from cronwrap.cost import (
    _parse_rate,
    cost_summary,
    load_costs,
    record_cost,
    save_costs,
    total_cost,
)
from cronwrap.cost_cli import build_cost_parser, cost_main


@pytest.fixture
def cfile(tmp_path):
    return str(tmp_path / "costs.json")


# --- _parse_rate ---

def test_parse_rate_per_second():
    assert _parse_rate("0.001/s") == pytest.approx(0.001)


def test_parse_rate_per_minute():
    assert _parse_rate("0.06/m") == pytest.approx(0.001)


def test_parse_rate_per_hour():
    assert _parse_rate("3.6/h") == pytest.approx(0.001)


def test_parse_rate_invalid_format():
    with pytest.raises(ValueError, match="Invalid rate format"):
        _parse_rate("0.001")


def test_parse_rate_unknown_unit():
    with pytest.raises(ValueError, match="Unknown rate unit"):
        _parse_rate("1.0/d")


# --- load / save ---

def test_load_costs_missing_file(cfile):
    assert load_costs(cfile) == {}


def test_load_costs_corrupt_file(cfile, tmp_path):
    (tmp_path / "costs.json").write_text("not-json")
    assert load_costs(cfile) == {}


def test_save_and_load_roundtrip(cfile):
    data = {"job1": [{"cost": 0.5, "currency": "USD"}]}
    save_costs(cfile, data)
    loaded = load_costs(cfile)
    assert loaded == data


def test_save_trims_to_max_entries(cfile):
    data = {"job1": [{"cost": i} for i in range(600)]}
    save_costs(cfile, data, max_entries=500)
    loaded = load_costs(cfile)
    assert len(loaded["job1"]) == 500


# --- record_cost ---

def test_record_cost_creates_entry(cfile):
    entry = record_cost(cfile, "job1", 100.0, "0.001/s")
    assert entry["cost"] == pytest.approx(0.1)
    assert entry["currency"] == "USD"


def test_record_cost_persists(cfile):
    record_cost(cfile, "job1", 60.0, "0.06/m")
    data = load_costs(cfile)
    assert len(data["job1"]) == 1
    assert data["job1"][0]["cost"] == pytest.approx(0.06)


def test_record_cost_accumulates(cfile):
    record_cost(cfile, "job1", 10.0, "0.001/s")
    record_cost(cfile, "job1", 20.0, "0.001/s")
    data = load_costs(cfile)
    assert len(data["job1"]) == 2


# --- total_cost / cost_summary ---

def test_total_cost_no_entries(cfile):
    assert total_cost(cfile, "job_missing") == 0.0


def test_total_cost_sums_correctly(cfile):
    record_cost(cfile, "job1", 100.0, "0.001/s")
    record_cost(cfile, "job1", 200.0, "0.001/s")
    assert total_cost(cfile, "job1") == pytest.approx(0.3)


def test_cost_summary_empty(cfile):
    s = cost_summary(cfile, "job_x")
    assert s == {"count": 0, "total": 0.0, "average": 0.0, "max": 0.0}


def test_cost_summary_values(cfile):
    record_cost(cfile, "job1", 100.0, "0.001/s")  # 0.1
    record_cost(cfile, "job1", 300.0, "0.001/s")  # 0.3
    s = cost_summary(cfile, "job1")
    assert s["count"] == 2
    assert s["total"] == pytest.approx(0.4)
    assert s["average"] == pytest.approx(0.2)
    assert s["max"] == pytest.approx(0.3)


# --- CLI ---

def _run(args):
    return cost_main(args)


def test_build_cost_parser_returns_parser():
    p = build_cost_parser()
    assert p is not None


def test_no_subcommand_returns_1(cfile):
    assert _run(["--file", cfile]) == 1


def test_show_exits_0(cfile):
    record_cost(cfile, "job1", 60.0, "0.001/s")
    assert _run(["--file", cfile, "show", "job1"]) == 0


def test_total_exits_0(cfile):
    record_cost(cfile, "job1", 60.0, "0.001/s")
    assert _run(["--file", cfile, "total", "job1"]) == 0


def test_list_exits_0(cfile):
    record_cost(cfile, "job1", 10.0, "0.001/s")
    assert _run(["--file", cfile, "list"]) == 0


def test_list_empty(cfile):
    assert _run(["--file", cfile, "list"]) == 0
