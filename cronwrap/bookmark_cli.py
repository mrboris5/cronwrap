"""CLI interface for job bookmarks."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from cronwrap.bookmark import add_bookmark, get_bookmark, list_bookmarks, remove_bookmark

_DEFAULT_PATH = "/var/lib/cronwrap/bookmarks.json"


def build_bookmark_parser(default_path: str = _DEFAULT_PATH) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-bookmark",
        description="Manage job bookmarks",
    )
    parser.add_argument("--file", default=default_path, metavar="PATH")
    sub = parser.add_subparsers(dest="subcommand")

    p_add = sub.add_parser("add", help="Add a bookmark")
    p_add.add_argument("job_id")
    p_add.add_argument("name")
    p_add.add_argument("value")

    p_get = sub.add_parser("get", help="Get a bookmark value")
    p_get.add_argument("job_id")
    p_get.add_argument("name")

    p_rm = sub.add_parser("remove", help="Remove a bookmark")
    p_rm.add_argument("job_id")
    p_rm.add_argument("name")

    p_ls = sub.add_parser("list", help="List bookmarks for a job")
    p_ls.add_argument("job_id")

    return parser


def bookmark_main(argv: Optional[List[str]] = None) -> int:
    parser = build_bookmark_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "add":
        entry = add_bookmark(args.job_id, args.name, args.value, args.file)
        print(f"Bookmark added: {entry['name']} = {entry['value']}")
        return 0

    if args.subcommand == "get":
        value = get_bookmark(args.job_id, args.name, args.file)
        if value is None:
            print(f"No bookmark '{args.name}' for job '{args.job_id}'")
            return 1
        print(value)
        return 0

    if args.subcommand == "remove":
        removed = remove_bookmark(args.job_id, args.name, args.file)
        if removed:
            print(f"Removed bookmark '{args.name}' for job '{args.job_id}'")
        else:
            print(f"No bookmark '{args.name}' found for job '{args.job_id}'")
        return 0 if removed else 1

    if args.subcommand == "list":
        entries = list_bookmarks(args.job_id, args.file)
        if not entries:
            print(f"No bookmarks for job '{args.job_id}'")
        for e in entries:
            print(f"  {e['name']}: {e['value']}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(bookmark_main())
