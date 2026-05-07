"""CLI for managing per-job retention policies."""
from __future__ import annotations

import argparse
import sys
from typing import Any

from cronwrap.retention_policy import (
    get_retention_policy,
    list_retention_policies,
    remove_retention_policy,
    set_retention_policy,
)

_DEFAULT_PATH = "/var/lib/cronwrap/retention_policies.json"


def _default_path() -> str:
    return _DEFAULT_PATH


def build_retention_policy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-retention-policy",
        description="Manage per-job retention policies.",
    )
    parser.add_argument("--file", default=_default_path(), help="Policy store path.")
    sub = parser.add_subparsers(dest="subcommand")

    p_set = sub.add_parser("set", help="Set a retention policy for a job.")
    p_set.add_argument("job_id")
    p_set.add_argument("--max-age-days", type=int, default=None)
    p_set.add_argument("--max-count", type=int, default=None)

    p_get = sub.add_parser("get", help="Show the retention policy for a job.")
    p_get.add_argument("job_id")

    p_rm = sub.add_parser("remove", help="Remove the retention policy for a job.")
    p_rm.add_argument("job_id")

    sub.add_parser("list", help="List all retention policies.")
    return parser


def _print_policy(job_id: str, policy: dict[str, Any]) -> None:
    print(f"job_id : {job_id}")
    print(f"  max_age_days : {policy.get('max_age_days', '-')}")
    print(f"  max_count    : {policy.get('max_count', '-')}")


def retention_policy_main(argv: list[str] | None = None) -> int:
    parser = build_retention_policy_parser()
    args = parser.parse_args(argv)
    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "set":
        entry = set_retention_policy(
            args.file, args.job_id,
            max_age_days=args.max_age_days,
            max_count=args.max_count,
        )
        _print_policy(args.job_id, entry)

    elif args.subcommand == "get":
        policy = get_retention_policy(args.file, args.job_id)
        if not policy:
            print(f"No retention policy for {args.job_id!r}.", file=sys.stderr)
            return 1
        _print_policy(args.job_id, policy)

    elif args.subcommand == "remove":
        removed = remove_retention_policy(args.file, args.job_id)
        if not removed:
            print(f"No retention policy for {args.job_id!r}.", file=sys.stderr)
            return 1
        print(f"Removed retention policy for {args.job_id!r}.")

    elif args.subcommand == "list":
        entries = list_retention_policies(args.file)
        if not entries:
            print("No retention policies defined.")
        for job_id, policy in entries:
            _print_policy(job_id, policy)
            print()

    return 0
