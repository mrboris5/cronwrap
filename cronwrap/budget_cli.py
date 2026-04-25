"""CLI sub-commands for inspecting and managing runtime budgets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwrap.budget import load_budgets, clear_budget, budget_reason

_DEFAULT_PATH = str(Path.home() / ".cronwrap" / "budgets.json")


def _default_path() -> str:
    return _DEFAULT_PATH


def build_budget_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(prog="cronwrap-budget", description="Manage job runtime budgets")
    parser.add_argument("--file", default=_default_path(), help="Budget state file")
    sub = parser.add_subparsers(dest="subcommand")

    lst = sub.add_parser("list", help="List all budget entries")
    lst.add_argument("--job", default=None, help="Filter by job ID")

    chk = sub.add_parser("check", help="Check if a job is over budget")
    chk.add_argument("job_id", help="Job identifier")
    chk.add_argument("budget", help="Budget duration e.g. 30s, 5m")

    clr = sub.add_parser("clear", help="Clear budget history for a job")
    clr.add_argument("job_id", help="Job identifier")

    return parser


def _print_entries(data: dict, job_filter: str | None) -> None:
    if not data:
        print("No budget entries found.")
        return
    for job_id, entry in sorted(data.items()):
        if job_filter and job_id != job_filter:
            continue
        count = entry.get("count", 0)
        avg = (entry["total"] / count) if count else 0.0
        print(f"{job_id}: samples={count}, avg={avg:.2f}s")


def budget_main(argv: list[str] | None = None) -> int:
    parser = build_budget_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "list":
        data = load_budgets(args.file)
        _print_entries(data, getattr(args, "job", None))
        return 0

    if args.subcommand == "check":
        reason = budget_reason(args.file, args.job_id, args.budget)
        if reason:
            print(f"OVER BUDGET: {reason}")
            return 1
        print(f"OK: '{args.job_id}' is within budget {args.budget}")
        return 0

    if args.subcommand == "clear":
        removed = clear_budget(args.file, args.job_id)
        if removed:
            print(f"Cleared budget history for '{args.job_id}'.")
        else:
            print(f"No budget entry found for '{args.job_id}'.")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(budget_main())
