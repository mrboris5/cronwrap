"""CLI for managing job quota policies."""

from __future__ import annotations

import argparse
import sys

from cronwrap.quota_policy import (
    get_quota,
    list_quotas,
    remove_quota,
    set_quota,
)

_DEFAULT_PATH = None  # resolved at runtime


def _default_path() -> str:
    import os
    return os.path.expanduser("~/.cronwrap/quota_policy.json")


def build_quota_policy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-quota-policy",
        description="Manage per-job run quota policies.",
    )
    parser.add_argument("--file", default=None, help="Path to quota policy file.")
    sub = parser.add_subparsers(dest="subcommand")

    p_set = sub.add_parser("set", help="Set a quota for a job.")
    p_set.add_argument("job_id")
    p_set.add_argument("max_runs", type=int)
    p_set.add_argument("period", help="Period, e.g. 1h, 24h, 7d")

    p_get = sub.add_parser("get", help="Show quota for a job.")
    p_get.add_argument("job_id")

    p_rm = sub.add_parser("remove", help="Remove quota for a job.")
    p_rm.add_argument("job_id")

    sub.add_parser("list", help="List all quota policies.")

    return parser


def quota_policy_main(argv=None) -> int:
    parser = build_quota_policy_parser()
    args = parser.parse_args(argv)
    path = args.file or _default_path()

    if args.subcommand == "set":
        entry = set_quota(args.job_id, args.max_runs, args.period, path=path)
        print(f"Quota set for '{args.job_id}': {entry['max_runs']} runs per {entry['period']}")
        return 0

    if args.subcommand == "get":
        entry = get_quota(args.job_id, path=path)
        if entry is None:
            print(f"No quota policy for '{args.job_id}'.")
            return 1
        print(f"{args.job_id}: {entry['max_runs']} runs per {entry['period']} (updated {entry['updated_at']})")
        return 0

    if args.subcommand == "remove":
        removed = remove_quota(args.job_id, path=path)
        if removed:
            print(f"Quota removed for '{args.job_id}'.")
            return 0
        print(f"No quota policy found for '{args.job_id}'.")
        return 1

    if args.subcommand == "list":
        data = list_quotas(path=path)
        if not data:
            print("No quota policies defined.")
            return 0
        for job_id, entry in sorted(data.items()):
            print(f"{job_id}: {entry['max_runs']} runs per {entry['period']}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(quota_policy_main())
