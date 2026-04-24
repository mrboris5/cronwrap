"""CLI sub-commands for incident management."""
from __future__ import annotations

import argparse
import os
import sys

from cronwrap.incident import active_incidents, close_incident, incident_history, open_incident

_DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".cronwrap", "incidents.json")


def _print_entry(entry: dict) -> None:
    status = entry.get("status", "?")
    job_id = entry.get("job_id", "?")
    opened = entry.get("opened_at", "?")
    closed = entry.get("closed_at") or "-"
    reason = entry.get("reason", "")
    resolution = entry.get("resolution", "")
    print(f"[{status.upper()}] {job_id}  opened={opened}  closed={closed}")
    if reason:
        print(f"  reason: {reason}")
    if resolution:
        print(f"  resolution: {resolution}")


def build_incident_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cronwrap-incident", description="Manage job incidents")
    parser.add_argument("--file", default=_DEFAULT_PATH, help="Incidents file path")
    sub = parser.add_subparsers(dest="subcommand")

    p_open = sub.add_parser("open", help="Open a new incident")
    p_open.add_argument("job_id", help="Job identifier")
    p_open.add_argument("reason", help="Reason for incident")

    p_close = sub.add_parser("close", help="Close the latest open incident for a job")
    p_close.add_argument("job_id", help="Job identifier")
    p_close.add_argument("--resolution", default="", help="Resolution note")

    p_list = sub.add_parser("list", help="List active (open) incidents")
    p_list.add_argument("--job", default=None, help="Filter by job id")

    p_hist = sub.add_parser("history", help="Show all incidents for a job")
    p_hist.add_argument("job_id", help="Job identifier")

    return parser


def incident_main(argv: list[str] | None = None) -> int:
    parser = build_incident_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    os.makedirs(os.path.dirname(args.file), exist_ok=True)

    if args.subcommand == "open":
        entry = open_incident(args.file, args.job_id, args.reason)
        print(f"Opened incident for '{args.job_id}': {entry['opened_at']}")

    elif args.subcommand == "close":
        entry = close_incident(args.file, args.job_id, args.resolution)
        if entry is None:
            print(f"No open incident found for '{args.job_id}'.")
            return 1
        print(f"Closed incident for '{args.job_id}': {entry['closed_at']}")

    elif args.subcommand == "list":
        entries = active_incidents(args.file, args.job)
        if not entries:
            print("No active incidents.")
        for e in entries:
            _print_entry(e)

    elif args.subcommand == "history":
        entries = incident_history(args.file, args.job_id)
        if not entries:
            print(f"No incidents found for '{args.job_id}'.")
        for e in entries:
            _print_entry(e)

    return 0


if __name__ == "__main__":
    sys.exit(incident_main())
