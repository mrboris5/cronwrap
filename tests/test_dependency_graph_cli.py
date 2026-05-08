"""Tests for cronwrap.dependency_graph_cli."""

import json
from pathlib import Path

import pytest

from cronwrap.dependency_graph_cli import build_dependency_graph_parser, dependency_graph_main


@pytest.fixture()
def gfile(tmp_path):
    return tmp_path / "depgraph.json"


def _run(gfile, *args):
    return dependency_graph_main(["--file", str(gfile), *args])


def _write(gfile, data):
    gfile.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------

def test_build_dependency_graph_parser_returns_parser():
    p = build_dependency_graph_parser()
    assert p is not None


def test_no_subcommand_returns_1(gfile):
    assert _run(gfile) == 1


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

def test_show_empty_graph(gfile, capsys):
    assert _run(gfile, "show") == 0
    out = capsys.readouterr().out
    assert "empty" in out


def test_show_with_jobs(gfile, capsys):
    _write(gfile, {"deploy": ["build"]})
    assert _run(gfile, "show") == 0
    out = capsys.readouterr().out
    assert "deploy" in out
    assert "build" in out


# ---------------------------------------------------------------------------
# sort
# ---------------------------------------------------------------------------

def test_sort_linear_order(gfile, capsys):
    _write(gfile, {"b": ["a"], "c": ["b"]})
    assert _run(gfile, "sort") == 0
    out = capsys.readouterr().out
    assert out.index("a") < out.index("b") < out.index("c")


def test_sort_cycle_returns_2(gfile):
    _write(gfile, {"a": ["b"], "b": ["a"]})
    assert _run(gfile, "sort") == 2


def test_sort_quiet_flag(gfile, capsys):
    _write(gfile, {"b": ["a"]})
    assert _run(gfile, "sort", "--quiet") == 0
    out = capsys.readouterr().out
    assert "Topological" not in out


# ---------------------------------------------------------------------------
# dependents
# ---------------------------------------------------------------------------

def test_dependents_direct(gfile, capsys):
    _write(gfile, {"b": ["a"], "c": ["a"]})
    assert _run(gfile, "dependents", "a") == 0
    out = capsys.readouterr().out
    assert "b" in out
    assert "c" in out


def test_dependents_all_transitive(gfile, capsys):
    _write(gfile, {"b": ["a"], "c": ["b"]})
    assert _run(gfile, "dependents", "a", "--all") == 0
    out = capsys.readouterr().out
    assert "b" in out
    assert "c" in out


def test_dependents_none_found(gfile, capsys):
    _write(gfile, {"b": ["a"]})
    assert _run(gfile, "dependents", "b") == 0
    out = capsys.readouterr().out
    assert "No dependents" in out
