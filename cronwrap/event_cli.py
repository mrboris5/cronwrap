"""CLI interface for the event log."""

import argparse
import sys
from typing import List, Optional

from cronwrap.event import clear_events, get_events, record_event

_DEFAULT_PATH = "/var/lib/cronwrap/events.json"


def _print_entry(entry: dict) -> None:
    ts = entry.get("timestamp", "?")
    etype = entry.get("event_type", "?")
    msg = entry.get("message", "")
    print(f"[{ts}] {etype}: {msg}")


def build_event_parser(argv: Optional[List[str]] = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-event",
        description="Manage the cronwrap event log",
    )
    parser.add_argument("--file", default=_DEFAULT_PATH, help="Event log file")
    sub = parser.add_subparsers(dest="subcommand")

    rec = sub.add_parser("record", help="Record a new event")
    rec.add_argument("job_id")
    rec.add_argument("event_type")
    rec.add_argument("message")

    lst = sub.add_parser("list", help="List events for a job")
    lst.add_argument("job_id")
    lst.add_argument("--type", dest="event_type", default=None)
    lst.add_argument("--limit", type=int, default=20)

    clr = sub.add_parser("clear", help="Clear all events for a job")
    clr.add_argument("job_id")

    return parser


def event_main(argv: Optional[List[str]] = None) -> int:
    parser = build_event_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "record":
        entry = record_event(
            args.job_id, args.event_type, args.message, args.file
        )
        _print_entry(entry)
        return 0

    if args.subcommand == "list":
        events = get_events(
            args.job_id, args.file,
            event_type=args.event_type,
            limit=args.limit,
        )
        if not events:
            print(f"No events found for '{args.job_id}'.")
        for e in events:
            _print_entry(e)
        return 0

    if args.subcommand == "clear":
        n = clear_events(args.job_id, args.file)
        print(f"Cleared {n} event(s) for '{args.job_id}'.")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(event_main())
