"""CLI sub-commands for managing job alert suppressions."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from cronwrap.suppression import (
    is_suppressed,
    list_suppressions,
    suppress_job,
    suppression_reason,
    unsuppress_job,
)

_DEFAULT_PATH = "/var/lib/cronwrap/suppressions.json"


def _parse_duration(value: str) -> int:
    """Parse '30s', '5m', '2h', '1d' into seconds."""
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if value and value[-1] in units:
        try:
            return int(value[:-1]) * units[value[-1]]
        except ValueError:
            pass
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid duration: {value!r}")


def _print_entry(entry: dict) -> None:
    print(f"  job_id : {entry.get('job_id', '-')}")
    print(f"  until  : {entry.get('until', '-')}")
    reason = entry.get("reason", "")
    if reason:
        print(f"  reason : {reason}")
    print()


def build_suppression_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwrap suppression",
        description="Manage alert suppressions for cron jobs.",
    )
    p.add_argument("--file", default=_DEFAULT_PATH, help="Suppression state file")
    sub = p.add_subparsers(dest="subcommand")

    add = sub.add_parser("add", help="Suppress a job's alerts")
    add.add_argument("job_id", help="Job identifier")
    add.add_argument("duration", type=_parse_duration, help="Duration e.g. 30m, 2h")
    add.add_argument("--reason", default="", help="Optional reason")

    rm = sub.add_parser("remove", help="Remove suppression for a job")
    rm.add_argument("job_id", help="Job identifier")

    chk = sub.add_parser("check", help="Check if a job is suppressed")
    chk.add_argument("job_id", help="Job identifier")

    sub.add_parser("list", help="List all active suppressions")
    return p


def suppression_main(argv: Optional[List[str]] = None) -> int:
    parser = build_suppression_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "add":
        entry = suppress_job(args.file, args.job_id, args.duration, args.reason)
        print(f"Suppressed {args.job_id} until {entry['until']}")
        return 0

    if args.subcommand == "remove":
        removed = unsuppress_job(args.file, args.job_id)
        if removed:
            print(f"Suppression removed for {args.job_id}")
        else:
            print(f"No active suppression found for {args.job_id}")
        return 0

    if args.subcommand == "check":
        reason = suppression_reason(args.file, args.job_id)
        if reason:
            print(f"{args.job_id}: {reason}")
            return 0
        print(f"{args.job_id}: not suppressed")
        return 0

    if args.subcommand == "list":
        entries = list_suppressions(args.file)
        if not entries:
            print("No active suppressions.")
        else:
            print(f"{len(entries)} active suppression(s):")
            for e in entries:
                _print_entry(e)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(suppression_main())
