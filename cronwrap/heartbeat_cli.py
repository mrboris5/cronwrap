"""CLI sub-commands for heartbeat management."""

from __future__ import annotations

import argparse
import sys

from cronwrap.heartbeat import (
    load_heartbeats,
    record_heartbeat,
    last_heartbeat,
    is_stale,
    stale_jobs,
)

_DEFAULT_FILE = "/var/lib/cronwrap/heartbeats.json"


def _print_entry(entry: dict) -> None:
    print(f"  job_id   : {entry['job_id']}")
    print(f"  last_seen: {entry['last_seen']}")
    if entry.get("meta"):
        print(f"  meta     : {entry['meta']}")


def build_heartbeat_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwrap-heartbeat",
        description="Manage job heartbeats",
    )
    p.add_argument("--file", default=_DEFAULT_FILE, help="Heartbeat store path")
    sub = p.add_subparsers(dest="subcmd")

    # ping
    ping = sub.add_parser("ping", help="Record a heartbeat for a job")
    ping.add_argument("job_id")
    ping.add_argument("--meta", nargs="*", metavar="KEY=VALUE", default=[])

    # show
    show = sub.add_parser("show", help="Show last heartbeat for a job")
    show.add_argument("job_id")

    # stale
    stale = sub.add_parser("stale", help="List jobs with stale heartbeats")
    stale.add_argument("--max-age", type=float, default=3600,
                       metavar="SECONDS", help="Age threshold in seconds (default 3600)")

    # list
    sub.add_parser("list", help="List all heartbeat records")

    return p


def heartbeat_main(argv: list | None = None) -> int:
    parser = build_heartbeat_parser()
    args = parser.parse_args(argv)

    if args.subcmd is None:
        parser.print_help()
        return 1

    if args.subcmd == "ping":
        meta = {}
        for pair in args.meta:
            if "=" in pair:
                k, v = pair.split("=", 1)
                meta[k] = v
        entry = record_heartbeat(args.file, args.job_id, meta or None)
        print(f"Heartbeat recorded for '{args.job_id}' at {entry['last_seen']}")
        return 0

    if args.subcmd == "show":
        entry = last_heartbeat(args.file, args.job_id)
        if entry is None:
            print(f"No heartbeat found for '{args.job_id}'")
            return 1
        _print_entry(entry)
        return 0

    if args.subcmd == "stale":
        jobs = stale_jobs(args.file, args.max_age)
        if not jobs:
            print("No stale jobs.")
        else:
            print(f"Stale jobs (>{args.max_age}s):")
            for j in jobs:
                print(f"  {j}")
        return 0

    if args.subcmd == "list":
        records = load_heartbeats(args.file)
        if not records:
            print("No heartbeat records.")
        else:
            for entry in records.values():
                _print_entry(entry)
                print()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(heartbeat_main())
