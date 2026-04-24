"""CLI sub-commands for managing runbooks."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from cronwrap.runbook import (
    get_runbook,
    list_runbooks,
    remove_runbook,
    set_runbook,
)

_DEFAULT_FILE = "/var/lib/cronwrap/runbooks.json"


def build_runbook_parser(argv: Optional[List[str]] = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-runbook",
        description="Manage runbook entries for cron jobs.",
    )
    parser.add_argument("--file", default=_DEFAULT_FILE, help="Runbook store path")
    sub = parser.add_subparsers(dest="cmd")

    # set
    p_set = sub.add_parser("set", help="Create or update a runbook entry")
    p_set.add_argument("job_id")
    p_set.add_argument("--url", default=None)
    p_set.add_argument("--notes", default=None)
    p_set.add_argument("--owner", default=None)
    p_set.add_argument("--escalation-contact", dest="escalation_contact", default=None)

    # get
    p_get = sub.add_parser("get", help="Show runbook entry for a job")
    p_get.add_argument("job_id")

    # remove
    p_rm = sub.add_parser("remove", help="Delete a runbook entry")
    p_rm.add_argument("job_id")

    # list
    sub.add_parser("list", help="List all job IDs with runbook entries")

    return parser


def runbook_main(argv: Optional[List[str]] = None) -> int:
    parser = build_runbook_parser()
    args = parser.parse_args(argv)

    if not args.cmd:
        parser.print_help()
        return 1

    if args.cmd == "set":
        entry = set_runbook(
            args.file,
            args.job_id,
            url=args.url,
            notes=args.notes,
            owner=args.owner,
            escalation_contact=args.escalation_contact,
        )
        print(f"Updated runbook for '{args.job_id}':")
        for k, v in entry.items():
            print(f"  {k}: {v}")
        return 0

    if args.cmd == "get":
        entry = get_runbook(args.file, args.job_id)
        if entry is None:
            print(f"No runbook found for '{args.job_id}'.")
            return 1
        for k, v in entry.items():
            print(f"{k}: {v}")
        return 0

    if args.cmd == "remove":
        removed = remove_runbook(args.file, args.job_id)
        if not removed:
            print(f"No runbook entry for '{args.job_id}'.")
            return 1
        print(f"Removed runbook for '{args.job_id}'.")
        return 0

    if args.cmd == "list":
        ids = list_runbooks(args.file)
        if not ids:
            print("No runbook entries found.")
        else:
            for job_id in ids:
                print(job_id)
        return 0

    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(runbook_main())
