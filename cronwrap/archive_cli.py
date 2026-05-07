"""CLI interface for the cronwrap archive module."""
from __future__ import annotations

import argparse
import json
import sys

from cronwrap.archive import (
    DEFAULT_MAX_AGE_DAYS,
    archive_summary,
    read_archive,
    write_archive,
)


def _default_path() -> str:
    return "/var/lib/cronwrap/archive.jsonl.gz"


def build_archive_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-archive",
        description="Manage cronwrap job run archives",
    )
    parser.add_argument("--file", default=_default_path(), help="Archive file path")
    sub = parser.add_subparsers(dest="subcommand")

    show = sub.add_parser("show", help="Show archive summary")
    show.add_argument("--json", dest="as_json", action="store_true")

    read = sub.add_parser("read", help="Read and print archive entries")
    read.add_argument("--limit", type=int, default=20)
    read.add_argument("--json", dest="as_json", action="store_true")

    write = sub.add_parser("write", help="Write a JSON entry to the archive")
    write.add_argument("entry", help="JSON string to archive")

    return parser


def archive_main(argv: list[str] | None = None) -> int:
    parser = build_archive_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "show":
        summary = archive_summary(args.file)
        if args.as_json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"Archive : {summary['path']}")
            print(f"Entries : {summary['entry_count']}")
            print(f"Size    : {summary['file_size_bytes']} bytes")
        return 0

    if args.subcommand == "read":
        entries = read_archive(args.file)
        entries = entries[-args.limit:]
        if args.as_json:
            print(json.dumps(entries, indent=2))
        else:
            for e in entries:
                print(json.dumps(e))
        return 0

    if args.subcommand == "write":
        try:
            entry = json.loads(args.entry)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON: {exc}", file=sys.stderr)
            return 2
        written = write_archive(args.file, [entry])
        print(f"Archived {written} entry.")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(archive_main())
