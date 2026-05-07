"""CLI interface for the watchdog module."""

import argparse
import sys
from cronwrap.watchdog import (
    load_watchdog,
    register_watchdog,
    checkin,
    is_overdue,
    overdue_reason,
)

_DEFAULT_PATH = "/var/lib/cronwrap/watchdog.json"


def _print_entry(job_id: str, entry: dict) -> None:
    print(f"  job_id     : {job_id}")
    print(f"  interval   : {entry.get('interval')}")
    print(f"  grace      : {entry.get('grace')}")
    print(f"  last_seen  : {entry.get('last_seen')}")
    print(f"  registered : {entry.get('registered_at')}")


def build_watchdog_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-watchdog", description="Watchdog management")
    p.add_argument("--file", default=_DEFAULT_PATH, help="Watchdog state file")
    sub = p.add_subparsers(dest="subcommand")

    reg = sub.add_parser("register", help="Register a job with an expected interval")
    reg.add_argument("job_id")
    reg.add_argument("interval", help="Expected run interval, e.g. 1h, 30m")
    reg.add_argument("--grace", default="5m", help="Grace period after interval (default: 5m)")

    ci = sub.add_parser("checkin", help="Record a check-in for a job")
    ci.add_argument("job_id")

    chk = sub.add_parser("check", help="Check if a job is overdue")
    chk.add_argument("job_id")

    ls = sub.add_parser("list", help="List all watched jobs")

    return p


def watchdog_main(argv=None) -> int:
    parser = build_watchdog_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "register":
        entry = register_watchdog(args.file, args.job_id, args.interval, args.grace)
        print(f"Registered watchdog for '{args.job_id}'.")
        _print_entry(args.job_id, entry)
        return 0

    if args.subcommand == "checkin":
        entry = checkin(args.file, args.job_id)
        print(f"Check-in recorded for '{args.job_id}' at {entry['last_seen']}.")
        return 0

    if args.subcommand == "check":
        reason = overdue_reason(args.file, args.job_id)
        if reason:
            print(f"OVERDUE: {reason}")
            return 2
        print(f"OK: '{args.job_id}' is not overdue.")
        return 0

    if args.subcommand == "list":
        state = load_watchdog(args.file)
        if not state:
            print("No jobs registered.")
            return 0
        for job_id, entry in state.items():
            overdue = is_overdue(args.file, job_id)
            status = "OVERDUE" if overdue else "OK"
            print(f"[{status}] {job_id}")
            _print_entry(job_id, entry)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(watchdog_main())
