"""Tests for cronwrap.dependency_graph."""

import pytest

from cronwrap.dependency_graph import (
    CycleError,
    all_dependents,
    build_graph,
    direct_dependents,
    graph_summary,
    topological_sort,
)


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------

def test_build_graph_returns_copy():
    src = {"a": ["b"]}
    g = build_graph(src)
    src["a"].append("c")
    assert g["a"] == ["b"]


def test_build_graph_empty():
    assert build_graph({}) == {}


# ---------------------------------------------------------------------------
# topological_sort
# ---------------------------------------------------------------------------

def test_topological_sort_linear():
    graph = {"b": ["a"], "c": ["b"]}
    order = topological_sort(graph)
    assert order.index("a") < order.index("b") < order.index("c")


def test_topological_sort_no_deps():
    graph = {"a": [], "b": [], "c": []}
    order = topological_sort(graph)
    assert set(order) == {"a", "b", "c"}


def test_topological_sort_cycle_raises():
    graph = {"a": ["b"], "b": ["a"]}
    with pytest.raises(CycleError):
        topological_sort(graph)


def test_topological_sort_self_cycle_raises():
    graph = {"a": ["a"]}
    with pytest.raises(CycleError):
        topological_sort(graph)


def test_topological_sort_includes_implicit_nodes():
    graph = {"b": ["a"]}  # 'a' never appears as a key
    order = topological_sort(graph)
    assert "a" in order and "b" in order
    assert order.index("a") < order.index("b")


# ---------------------------------------------------------------------------
# direct_dependents
# ---------------------------------------------------------------------------

def test_direct_dependents_found():
    graph = {"b": ["a"], "c": ["a"], "d": ["b"]}
    result = direct_dependents("a", graph)
    assert set(result) == {"b", "c"}


def test_direct_dependents_none():
    graph = {"b": ["a"]}
    assert direct_dependents("b", graph) == []


# ---------------------------------------------------------------------------
# all_dependents
# ---------------------------------------------------------------------------

def test_all_dependents_transitive():
    graph = {"b": ["a"], "c": ["b"], "d": ["c"]}
    result = all_dependents("a", graph)
    assert set(result) == {"b", "c", "d"}


def test_all_dependents_none():
    graph = {"b": ["a"]}
    assert all_dependents("b", graph) == []


# ---------------------------------------------------------------------------
# graph_summary
# ---------------------------------------------------------------------------

def test_graph_summary_empty():
    assert graph_summary({}) == "Dependency graph: (empty)"


def test_graph_summary_contains_job():
    graph = {"deploy": ["build"]}
    summary = graph_summary(graph)
    assert "deploy" in summary
    assert "build" in summary


def test_graph_summary_no_deps_label():
    graph = {"standalone": []}
    assert "(none)" in graph_summary(graph)
