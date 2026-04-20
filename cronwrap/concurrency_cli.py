"""CLI sub-commands for inspecting and managing concurrency state.

Usage examples:
    cronwrap-concurrency list  --state /var/run/myjob.json
    cronwrap-concurrency clear --state /var/run/myjob.json
"""

from __future__ import annotations

import argparse
import os
import sys

from cronwrap.concurrency import (
    load_active,
    prune_dead,
    save_active,
)


def _print_pids(pids: list[int]) -> None:
    if not pids:
        print("No active PIDs recorded.")
    else:
        print(f"{len(pids)} active PID(s):")
        for pid in pids:
            print(f"  {pid}")


def build_concurrency_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-concurrency",
        description="Inspect and manage cronwrap concurrency state.",
    )
    parser.add_argument(
        "--state",
        required=True,
        metavar="FILE",
        help="Path to the concurrency state JSON file.",
    )

    sub = parser.add_subparsers(dest="subcommand")

    sub.add_parser("list", help="List currently active PIDs (pruning dead ones).")

    sub.add_parser(
        "clear",
        help="Remove all recorded PIDs (including live ones).",
    )

    prune_p = sub.add_parser(
        "prune",
        help="Remove dead PIDs and rewrite the state file.",
    )

    return parser


def concurrency_main(argv: list[str] | None = None) -> int:
    parser = build_concurrency_parser()
    args = parser.parse_args(argv)

    if args.subcommand is None:
        parser.print_help()
        return 1

    if args.subcommand == "list":
        pids = prune_dead(load_active(args.state))
        _print_pids(pids)
        return 0

    if args.subcommand == "clear":
        save_active(args.state, [])
        print("Concurrency state cleared.")
        return 0

    if args.subcommand == "prune":
        before = load_active(args.state)
        after = prune_dead(before)
        save_active(args.state, after)
        removed = len(before) - len(after)
        print(f"Pruned {removed} dead PID(s). {len(after)} remaining.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(concurrency_main())
