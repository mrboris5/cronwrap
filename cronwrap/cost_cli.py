"""CLI for inspecting job cost records."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwrap.cost import cost_summary, load_costs, total_cost


def _default_path() -> str:
    return str(Path.home() / ".cronwrap" / "costs.json")


def build_cost_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-cost",
        description="Inspect compute cost records for cron jobs.",
    )
    parser.add_argument("--file", default=_default_path(), help="Path to costs JSON file")
    sub = parser.add_subparsers(dest="subcommand")

    show = sub.add_parser("show", help="Show cost summary for a job")
    show.add_argument("job_id", help="Job identifier")

    total = sub.add_parser("total", help="Print total cost for a job")
    total.add_argument("job_id", help="Job identifier")

    sub.add_parser("list", help="List all jobs with recorded costs")

    return parser


def _print_summary(job_id: str, summary: dict) -> None:
    print(f"Job:     {job_id}")
    print(f"Runs:    {summary['count']}")
    print(f"Total:   {summary['total']}")
    print(f"Average: {summary['average']}")
    print(f"Max:     {summary['max']}")


def cost_main(argv: list[str] | None = None) -> int:
    parser = build_cost_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "show":
        from cronwrap.cost import cost_summary as cs
        summary = cs(args.file, args.job_id)
        _print_summary(args.job_id, summary)
        return 0

    if args.subcommand == "total":
        t = total_cost(args.file, args.job_id)
        print(f"{args.job_id}: {t}")
        return 0

    if args.subcommand == "list":
        data = load_costs(args.file)
        if not data:
            print("No cost records found.")
            return 0
        for job_id, entries in sorted(data.items()):
            t = round(sum(e["cost"] for e in entries), 6)
            print(f"{job_id}: {len(entries)} run(s), total={t}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(cost_main())
