"""CLI interface for cronwrap healthcheck management."""

import argparse
import os
import sys

from cronwrap.healthcheck import (
    all_job_ids,
    is_healthy,
    last_ping,
    load_healthchecks,
    record_ping,
)

_DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".cronwrap", "healthchecks.json")


def _print_entry(entry: dict) -> None:
    print(f"  job_id   : {entry['job_id']}")
    print(f"  status   : {entry['status']}")
    print(f"  timestamp: {entry['timestamp']}")
    if entry.get("detail"):
        print(f"  detail   : {entry['detail']}")


def build_healthcheck_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-healthcheck",
        description="Manage cronwrap job healthcheck pings.",
    )
    parser.add_argument("--file", default=_DEFAULT_PATH, help="Healthcheck state file.")
    sub = parser.add_subparsers(dest="subcommand")

    ping_p = sub.add_parser("ping", help="Record a healthcheck ping.")
    ping_p.add_argument("job_id", help="Job identifier.")
    ping_p.add_argument(
        "--status",
        choices=["ok", "fail", "warn"],
        default="ok",
        help="Ping status (default: ok).",
    )
    ping_p.add_argument("--detail", default="", help="Optional detail message.")

    show_p = sub.add_parser("show", help="Show the last ping for a job.")
    show_p.add_argument("job_id", help="Job identifier.")

    sub.add_parser("list", help="List all jobs with healthcheck records.")

    status_p = sub.add_parser("status", help="Print overall health status.")
    status_p.add_argument("job_id", nargs="?", help="Specific job (omit for all).")

    return parser


def healthcheck_main(argv=None) -> int:
    parser = build_healthcheck_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    path = args.file
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if args.subcommand == "ping":
        entry = record_ping(path, args.job_id, status=args.status, detail=args.detail)
        print(f"Recorded ping for '{args.job_id}': {entry['status']} at {entry['timestamp']}")
        return 0

    if args.subcommand == "show":
        entry = last_ping(path, args.job_id)
        if entry is None:
            print(f"No healthcheck records for '{args.job_id}'.")
            return 1
        _print_entry(entry)
        return 0

    if args.subcommand == "list":
        ids = all_job_ids(path)
        if not ids:
            print("No healthcheck records found.")
        else:
            for jid in ids:
                print(jid)
        return 0

    if args.subcommand == "status":
        job_id = getattr(args, "job_id", None)
        ids = [job_id] if job_id else all_job_ids(path)
        if not ids:
            print("No healthcheck records found.")
            return 0
        all_ok = True
        for jid in ids:
            healthy = is_healthy(path, jid)
            state = "OK" if healthy else "FAIL"
            print(f"{jid}: {state}")
            if not healthy:
                all_ok = False
        return 0 if all_ok else 2

    return 1


if __name__ == "__main__":
    sys.exit(healthcheck_main())
