"""CLI interface for blackout window management."""

from __future__ import annotations

import argparse
import sys
from datetime import timezone

from cronwrap.blackout import (
    add_blackout,
    get_blackouts,
    is_blacked_out,
    remove_blackout,
)

_DEFAULT_PATH = "/var/lib/cronwrap/blackouts.json"


def _print_windows(job_id: str, windows: list) -> None:
    if not windows:
        print(f"No blackout windows for {job_id!r}")
        return
    print(f"Blackout windows for {job_id!r}:")
    for i, w in enumerate(windows):
        reason = f" — {w['reason']}" if w.get("reason") else ""
        print(f"  [{i}] {w['start']}  →  {w['end']}{reason}")


def build_blackout_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-blackout",
        description="Manage blackout windows for cron jobs",
    )
    parser.add_argument("--file", default=_DEFAULT_PATH, help="Blackout store path")
    sub = parser.add_subparsers(dest="subcommand")

    add_p = sub.add_parser("add", help="Add a blackout window")
    add_p.add_argument("job_id")
    add_p.add_argument("start", help="ISO datetime start")
    add_p.add_argument("end", help="ISO datetime end")
    add_p.add_argument("--reason", default="", help="Human-readable reason")

    rm_p = sub.add_parser("remove", help="Remove a blackout window by index")
    rm_p.add_argument("job_id")
    rm_p.add_argument("index", type=int)

    ls_p = sub.add_parser("list", help="List blackout windows for a job")
    ls_p.add_argument("job_id")

    chk_p = sub.add_parser("check", help="Check if a job is currently blacked out")
    chk_p.add_argument("job_id")

    return parser


def blackout_main(argv=None) -> int:
    parser = build_blackout_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "add":
        entry = add_blackout(args.file, args.job_id, args.start, args.end, args.reason)
        print(f"Added blackout: {entry['start']} → {entry['end']}")
        return 0

    if args.subcommand == "remove":
        ok = remove_blackout(args.file, args.job_id, args.index)
        if ok:
            print(f"Removed blackout [{args.index}] for {args.job_id!r}")
            return 0
        print(f"Index {args.index} not found for {args.job_id!r}", file=sys.stderr)
        return 1

    if args.subcommand == "list":
        windows = get_blackouts(args.file, args.job_id)
        _print_windows(args.job_id, windows)
        return 0

    if args.subcommand == "check":
        if is_blacked_out(args.file, args.job_id):
            print(f"{args.job_id!r} is currently blacked out")
            return 1
        print(f"{args.job_id!r} is not blacked out")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(blackout_main())
