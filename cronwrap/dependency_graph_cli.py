"""CLI interface for inspecting the job dependency graph."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cronwrap.dependency_graph import (
    CycleError,
    all_dependents,
    build_graph,
    direct_dependents,
    graph_summary,
    topological_sort,
)


def _default_path() -> str:
    return str(Path.home() / ".cronwrap" / "dependency_graph.json")


def _load_graph(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def build_dependency_graph_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-depgraph",
        description="Inspect the job dependency graph.",
    )
    parser.add_argument("--file", default=_default_path(), help="Graph JSON file")
    sub = parser.add_subparsers(dest="subcmd")

    sub.add_parser("show", help="Print the full dependency graph")

    sort_p = sub.add_parser("sort", help="Print jobs in topological order")
    sort_p.add_argument("--quiet", action="store_true")

    dep_p = sub.add_parser("dependents", help="List dependents of a job")
    dep_p.add_argument("job_id")
    dep_p.add_argument("--all", dest="all_deps", action="store_true")

    return parser


def dependency_graph_main(argv=None) -> int:
    parser = build_dependency_graph_parser()
    args = parser.parse_args(argv)
    if not args.subcmd:
        parser.print_help()
        return 1

    graph = build_graph(_load_graph(args.file))

    if args.subcmd == "show":
        print(graph_summary(graph))
        return 0

    if args.subcmd == "sort":
        try:
            order = topological_sort(graph)
        except CycleError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if args.quiet:
            print("\n".join(order))
        else:
            print("Topological order:")
            for i, job in enumerate(order, 1):
                print(f"  {i}. {job}")
        return 0

    if args.subcmd == "dependents":
        if args.all_deps:
            result = all_dependents(args.job_id, graph)
        else:
            result = direct_dependents(args.job_id, graph)
        if not result:
            print(f"No dependents found for '{args.job_id}'.")
        else:
            for job in result:
                print(job)
        return 0

    return 1
