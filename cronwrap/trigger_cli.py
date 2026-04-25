"""CLI interface for job trigger management."""

import argparse
import json
import sys
from typing import List

from cronwrap.trigger import (
    acknowledge_trigger,
    last_trigger,
    pending_triggers,
    record_trigger,
)

_DEFAULT_PATH = "/var/lib/cronwrap/triggers.json"


def _print_entry(entry: dict) -> None:
    ack = "[ack]" if entry.get("acknowledged") else "[pending]"
    print(
        f"{ack} {entry.get('triggered_at', '')}  "
        f"job={entry.get('job_id', '')}  "
        f"type={entry.get('trigger_type', '')}  "
        f"source={entry.get('source', '')}  "
        f"reason={entry.get('reason', '')}"
    )


def build_trigger_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-trigger",
        description="Manage manual and event-based job triggers",
    )
    parser.add_argument("--file", default=_DEFAULT_PATH, help="Trigger store path")
    sub = parser.add_subparsers(dest="subcommand")

    fire = sub.add_parser("fire", help="Record a trigger event")
    fire.add_argument("job_id")
    fire.add_argument("--type", dest="trigger_type", default="manual")
    fire.add_argument("--source", default="cli")
    fire.add_argument("--reason", default="")

    ack = sub.add_parser("ack", help="Acknowledge latest trigger for a job")
    ack.add_argument("job_id")

    pending = sub.add_parser("pending", help="List unacknowledged triggers")
    pending.add_argument("--job", dest="job_id", default=None)

    last = sub.add_parser("last", help="Show last trigger for a job")
    last.add_argument("job_id")

    return parser


def trigger_main(argv: List[str] = None) -> int:
    parser = build_trigger_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "fire":
        entry = record_trigger(
            args.file, args.job_id, args.trigger_type, args.source, args.reason
        )
        print(f"Trigger recorded for job '{args.job_id}' at {entry['triggered_at']}")
        return 0

    if args.subcommand == "ack":
        ok = acknowledge_trigger(args.file, args.job_id)
        if ok:
            print(f"Acknowledged latest trigger for '{args.job_id}'")
            return 0
        print(f"No pending trigger found for '{args.job_id}'", file=sys.stderr)
        return 1

    if args.subcommand == "pending":
        entries = pending_triggers(args.file, args.job_id)
        if not entries:
            print("No pending triggers.")
        for e in entries:
            _print_entry(e)
        return 0

    if args.subcommand == "last":
        entry = last_trigger(args.file, args.job_id)
        if not entry:
            print(f"No triggers found for '{args.job_id}'", file=sys.stderr)
            return 1
        _print_entry(entry)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(trigger_main())
