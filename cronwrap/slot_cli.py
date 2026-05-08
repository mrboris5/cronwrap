"""CLI interface for slot usage inspection and management."""

from __future__ import annotations

import argparse
import sys
from typing import List

from cronwrap.slot import (
    load_slots,
    record_slot_use,
    reset_slots,
    uses_in_window,
    is_slot_exceeded,
)

_DEFAULT_PATH = "/var/lib/cronwrap/slots.json"


def _default_path() -> str:
    import os
    return os.environ.get("CRONWRAP_SLOT_FILE", _DEFAULT_PATH)


def build_slot_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cronwrap-slot", description="Manage job execution slots")
    sub = parser.add_subparsers(dest="subcommand")

    show = sub.add_parser("show", help="Show slot usage for a job")
    show.add_argument("job_id")
    show.add_argument("--window", default="1h")
    show.add_argument("--file", default=None)

    check = sub.add_parser("check", help="Check if slot limit is exceeded")
    check.add_argument("job_id")
    check.add_argument("--max", type=int, required=True)
    check.add_argument("--window", default="1h")
    check.add_argument("--file", default=None)

    rec = sub.add_parser("record", help="Record a slot use for a job")
    rec.add_argument("job_id")
    rec.add_argument("--file", default=None)

    rst = sub.add_parser("reset", help="Reset slot usage for a job")
    rst.add_argument("job_id")
    rst.add_argument("--file", default=None)

    return parser


def slot_main(argv: List[str] | None = None) -> int:
    parser = build_slot_parser()
    args = parser.parse_args(argv)
    if not args.subcommand:
        parser.print_help()
        return 1

    path = args.file or _default_path()

    if args.subcommand == "show":
        uses = uses_in_window(path, args.job_id, args.window)
        print(f"Job '{args.job_id}' — {len(uses)} use(s) in window '{args.window}'")
        for ts in uses:
            print(f"  {ts}")

    elif args.subcommand == "check":
        exceeded = is_slot_exceeded(path, args.job_id, args.max, args.window)
        status = "EXCEEDED" if exceeded else "OK"
        print(f"Slot check for '{args.job_id}': {status} ({args.max} max / {args.window})")
        return 1 if exceeded else 0

    elif args.subcommand == "record":
        record_slot_use(path, args.job_id)
        print(f"Recorded slot use for '{args.job_id}'.")

    elif args.subcommand == "reset":
        reset_slots(path, args.job_id)
        print(f"Reset slot usage for '{args.job_id}'.")

    return 0


if __name__ == "__main__":
    sys.exit(slot_main())
