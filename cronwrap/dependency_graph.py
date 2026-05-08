"""Dependency graph: build and traverse job dependency relationships."""

from __future__ import annotations

from typing import Dict, List, Set


class CycleError(Exception):
    """Raised when a cycle is detected in the dependency graph."""


def build_graph(jobs: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Return adjacency list from a mapping of job_id -> [dependency_ids]."""
    return {job: list(deps) for job, deps in jobs.items()}


def _visit(
    node: str,
    graph: Dict[str, List[str]],
    visited: Set[str],
    stack: Set[str],
    order: List[str],
) -> None:
    visited.add(node)
    stack.add(node)
    for dep in graph.get(node, []):
        if dep not in visited:
            _visit(dep, graph, visited, stack, order)
        elif dep in stack:
            raise CycleError(f"Cycle detected involving job '{dep}'")
    stack.discard(node)
    order.append(node)


def topological_sort(graph: Dict[str, List[str]]) -> List[str]:
    """Return jobs in dependency-first order. Raises CycleError on cycles."""
    visited: Set[str] = set()
    stack: Set[str] = set()
    order: List[str] = []
    all_nodes: Set[str] = set(graph.keys())
    for deps in graph.values():
        all_nodes.update(deps)
    for node in sorted(all_nodes):
        if node not in visited:
            _visit(node, graph, visited, stack, order)
    return order


def direct_dependents(job_id: str, graph: Dict[str, List[str]]) -> List[str]:
    """Return jobs that directly depend on *job_id*."""
    return [j for j, deps in graph.items() if job_id in deps]


def all_dependents(job_id: str, graph: Dict[str, List[str]]) -> List[str]:
    """Return all transitive dependents of *job_id* (breadth-first)."""
    result: List[str] = []
    queue = direct_dependents(job_id, graph)
    seen: Set[str] = set(queue)
    while queue:
        current = queue.pop(0)
        result.append(current)
        for nxt in direct_dependents(current, graph):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return result


def graph_summary(graph: Dict[str, List[str]]) -> str:
    """Return a human-readable summary of the dependency graph."""
    lines = []
    for job in sorted(graph):
        deps = graph[job]
        dep_str = ", ".join(deps) if deps else "(none)"
        lines.append(f"  {job} -> {dep_str}")
    return "Dependency graph:\n" + "\n".join(lines) if lines else "Dependency graph: (empty)"
