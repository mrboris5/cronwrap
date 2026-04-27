"""CLI sub-commands for managing execution policies."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cronwrap.policy import (
    apply_policy,
    get_policy,
    list_policies,
    remove_policy,
    set_policy,
)

_DEFAULT_PATH = Path(".cronwrap_policies.json")


def _default_path() -> Path:
    return _DEFAULT_PATH


def build_policy_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    p = parser or argparse.ArgumentParser(prog="cronwrap-policy", description="Manage job policies")
    p.add_argument("--file", type=Path, default=_default_path(), help="Policies file path")
    sub = p.add_subparsers(dest="subcommand")

    s = sub.add_parser("set", help="Create or replace a policy")
    s.add_argument("name", help="Policy name")
    s.add_argument("rules", help="JSON object of policy rules")

    sub.add_parser("list", help="List all policy names")

    g = sub.add_parser("get", help="Show a policy")
    g.add_argument("name")

    r = sub.add_parser("remove", help="Remove a policy")
    r.add_argument("name")

    a = sub.add_parser("apply", help="Merge policy into a job config and print result")
    a.add_argument("name", help="Policy name")
    a.add_argument("config", help="JSON job config")

    return p


def policy_main(argv: list[str] | None = None) -> int:
    parser = build_policy_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "set":
        try:
            rules = json.loads(args.rules)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON for rules: {exc}", file=sys.stderr)
            return 2
        set_policy(args.name, rules, args.file)
        print(f"Policy {args.name!r} saved.")
        return 0

    if args.subcommand == "list":
        names = list_policies(args.file)
        if not names:
            print("(no policies defined)")
        else:
            for n in names:
                print(n)
        return 0

    if args.subcommand == "get":
        policy = get_policy(args.name, args.file)
        if policy is None:
            print(f"Policy {args.name!r} not found.", file=sys.stderr)
            return 1
        print(json.dumps(policy, indent=2))
        return 0

    if args.subcommand == "remove":
        if not remove_policy(args.name, args.file):
            print(f"Policy {args.name!r} not found.", file=sys.stderr)
            return 1
        print(f"Policy {args.name!r} removed.")
        return 0

    if args.subcommand == "apply":
        try:
            job_cfg = json.loads(args.config)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON for config: {exc}", file=sys.stderr)
            return 2
        try:
            merged = apply_policy(args.name, job_cfg, args.file)
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(json.dumps(merged, indent=2))
        return 0

    return 1
