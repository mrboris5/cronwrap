"""CLI interface for the job changelog."""

import argparse
import sys
from typing import List

from cronwrap.changelog import clear_changelog, get_changes, record_change

_DEFAULT_PATH = "/var/lib/cronwrap/changelog.json"


def _print_entries(entries: List[dict]) -> None:
    if not entries:
        print("(no entries)")
        return
    for e in entries:
        author = e.get("author", "<unknown>")
        print(
            f"{e['timestamp']}  {e['job_id']}  {e['field']}  "
            f"{e['old_value']!r} -> {e['new_value']!r}  [{author}]"
        )


def build_changelog_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwrap-changelog", description="Manage job changelogs"
    )
    p.add_argument("--file", default=_DEFAULT_PATH, help="Changelog file path")
    sub = p.add_subparsers(dest="subcmd")

    rec = sub.add_parser("record", help="Record a configuration change")
    rec.add_argument("job_id")
    rec.add_argument("field")
    rec.add_argument("old_value")
    rec.add_argument("new_value")
    rec.add_argument("--author", default=None)

    show = sub.add_parser("show", help="Show changelog for a job")
    show.add_argument("job_id")
    show.add_argument("--field", default=None)

    clr = sub.add_parser("clear", help="Clear changelog entries for a job")
    clr.add_argument("job_id")

    return p


def changelog_main(argv=None) -> int:
    parser = build_changelog_parser()
    args = parser.parse_args(argv)

    if not args.subcmd:
        parser.print_help()
        return 1

    if args.subcmd == "record":
        entry = record_change(
            args.file,
            args.job_id,
            args.field,
            args.old_value,
            args.new_value,
            author=args.author,
        )
        print(f"Recorded: {entry['timestamp']}  {entry['field']}  {entry['old_value']!r} -> {entry['new_value']!r}")

    elif args.subcmd == "show":
        entries = get_changes(args.file, args.job_id, field=args.field)
        _print_entries(entries)

    elif args.subcmd == "clear":
        n = clear_changelog(args.file, args.job_id)
        print(f"Removed {n} entries for '{args.job_id}'.")

    return 0


if __name__ == "__main__":
    sys.exit(changelog_main())
