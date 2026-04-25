"""CLI sub-commands for job ownership management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwrap.ownership import (
    all_owners,
    get_owner,
    jobs_by_team,
    remove_owner,
    set_owner,
)

_DEFAULT_PATH = Path(".cronwrap_ownership.json")


def _print_entry(job_id: str, entry: dict) -> None:
    team = entry.get("team", "-")
    email = entry.get("email", "-")
    print(f"{job_id:30s}  owner={entry['owner']}  team={team}  email={email}")


def build_ownership_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    p = parser or argparse.ArgumentParser(prog="cronwrap ownership", description="Manage job ownership")
    p.add_argument("--file", default=str(_DEFAULT_PATH), help="Ownership store path")
    sub = p.add_subparsers(dest="subcmd")

    s = sub.add_parser("set", help="Assign owner to a job")
    s.add_argument("job_id")
    s.add_argument("owner")
    s.add_argument("--team", default=None)
    s.add_argument("--email", default=None)

    g = sub.add_parser("get", help="Show owner of a job")
    g.add_argument("job_id")

    r = sub.add_parser("remove", help="Remove ownership record")
    r.add_argument("job_id")

    t = sub.add_parser("team", help="List jobs belonging to a team")
    t.add_argument("team_name")

    sub.add_parser("list", help="List all ownership records")
    return p


def ownership_main(argv: list[str] | None = None) -> int:
    parser = build_ownership_parser()
    args = parser.parse_args(argv)
    path = Path(args.file)

    if args.subcmd == "set":
        entry = set_owner(args.job_id, args.owner, team=args.team, email=args.email, path=path)
        _print_entry(args.job_id, entry)
        return 0

    if args.subcmd == "get":
        entry = get_owner(args.job_id, path=path)
        if entry is None:
            print(f"No owner set for '{args.job_id}'.")
            return 1
        _print_entry(args.job_id, entry)
        return 0

    if args.subcmd == "remove":
        removed = remove_owner(args.job_id, path=path)
        print("Removed." if removed else f"No record for '{args.job_id}'.")
        return 0 if removed else 1

    if args.subcmd == "team":
        jobs = jobs_by_team(args.team_name, path=path)
        if not jobs:
            print(f"No jobs for team '{args.team_name}'.")
        for jid in jobs:
            print(jid)
        return 0

    if args.subcmd == "list":
        data = all_owners(path=path)
        if not data:
            print("No ownership records.")
        for jid, entry in sorted(data.items()):
            _print_entry(jid, entry)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(ownership_main())
