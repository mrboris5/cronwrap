"""CLI sub-commands for managing job aliases."""

import argparse
import sys
from pathlib import Path

from cronwrap.alias import (
    all_aliases,
    get_alias,
    remove_alias,
    resolve,
    set_alias,
)

_DEFAULT_PATH = Path(".cronwrap_aliases.json")


def build_alias_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap alias", description="Manage job aliases")
    p.add_argument("--file", type=Path, default=_DEFAULT_PATH, metavar="PATH")
    sub = p.add_subparsers(dest="subcmd")

    s = sub.add_parser("set", help="Create or update an alias")
    s.add_argument("alias", help="Short alias name")
    s.add_argument("job_id", help="Target job ID")

    g = sub.add_parser("get", help="Resolve an alias")
    g.add_argument("alias")

    r = sub.add_parser("remove", help="Delete an alias")
    r.add_argument("alias")

    sub.add_parser("list", help="List all aliases")

    rs = sub.add_parser("resolve", help="Resolve name, falling back to itself")
    rs.add_argument("name")

    return p


def alias_main(argv=None) -> int:
    parser = build_alias_parser()
    args = parser.parse_args(argv)

    if not args.subcmd:
        parser.print_help()
        return 1

    f = args.file

    if args.subcmd == "set":
        set_alias(args.alias, args.job_id, f)
        print(f"alias '{args.alias}' -> '{args.job_id}' saved.")

    elif args.subcmd == "get":
        job_id = get_alias(args.alias, f)
        if job_id is None:
            print(f"alias '{args.alias}' not found.", file=sys.stderr)
            return 1
        print(job_id)

    elif args.subcmd == "remove":
        if not remove_alias(args.alias, f):
            print(f"alias '{args.alias}' not found.", file=sys.stderr)
            return 1
        print(f"alias '{args.alias}' removed.")

    elif args.subcmd == "list":
        aliases = all_aliases(f)
        if not aliases:
            print("No aliases defined.")
        else:
            for alias, job_id in sorted(aliases.items()):
                print(f"{alias:30s} -> {job_id}")

    elif args.subcmd == "resolve":
        print(resolve(args.name, f))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(alias_main())
