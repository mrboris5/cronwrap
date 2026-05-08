"""CLI for job-scoped variable management."""
from __future__ import annotations

import argparse
import json
import sys

from cronwrap.variable import (
    clear_variables,
    get_all_variables,
    get_variable,
    remove_variable,
    set_variable,
)

_DEFAULT_PATH = "/var/lib/cronwrap/variables.json"


def build_variable_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwrap-variable",
        description="Manage per-job variables",
    )
    p.add_argument("--file", default=_DEFAULT_PATH, help="Variables storage file")
    sub = p.add_subparsers(dest="subcommand")

    s = sub.add_parser("set", help="Set a variable")
    s.add_argument("job_id")
    s.add_argument("key")
    s.add_argument("value")

    g = sub.add_parser("get", help="Get a variable")
    g.add_argument("job_id")
    g.add_argument("key")

    la = sub.add_parser("list", help="List all variables for a job")
    la.add_argument("job_id")

    rm = sub.add_parser("remove", help="Remove a variable")
    rm.add_argument("job_id")
    rm.add_argument("key")

    cl = sub.add_parser("clear", help="Clear all variables for a job")
    cl.add_argument("job_id")

    return p


def variable_main(argv: list[str] | None = None) -> int:
    parser = build_variable_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "set":
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        result = set_variable(args.file, args.job_id, args.key, value)
        print(f"Set {args.key}={result[args.key]!r} for job '{args.job_id}'")

    elif args.subcommand == "get":
        val = get_variable(args.file, args.job_id, args.key)
        if val is None:
            print(f"Variable '{args.key}' not found for job '{args.job_id}'")
            return 1
        print(json.dumps(val))

    elif args.subcommand == "list":
        variables = get_all_variables(args.file, args.job_id)
        if not variables:
            print(f"No variables for job '{args.job_id}'")
        else:
            for k, v in sorted(variables.items()):
                print(f"  {k} = {json.dumps(v)}")

    elif args.subcommand == "remove":
        removed = remove_variable(args.file, args.job_id, args.key)
        if removed:
            print(f"Removed '{args.key}' from job '{args.job_id}'")
        else:
            print(f"Variable '{args.key}' not found for job '{args.job_id}'")
            return 1

    elif args.subcommand == "clear":
        count = clear_variables(args.file, args.job_id)
        print(f"Cleared {count} variable(s) for job '{args.job_id}'")

    return 0


if __name__ == "__main__":
    sys.exit(variable_main())
