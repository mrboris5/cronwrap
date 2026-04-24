"""CLI sub-commands for inspecting captured job output."""

from __future__ import annotations

import argparse
import sys

from cronwrap.output import get_outputs, last_output

_DEFAULT_PATH = "/var/lib/cronwrap/outputs.json"


def _default_path() -> str:
    import os
    return os.environ.get("CRONWRAP_OUTPUT_FILE", _DEFAULT_PATH)


def build_output_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="cronwrap-output",
        description="Inspect captured cron job output",
    )
    parser.add_argument("--file", default=None, help="Output store path")
    sub = parser.add_subparsers(dest="subcmd")

    p_last = sub.add_parser("last", help="Show the most recent output for a job")
    p_last.add_argument("job_id", help="Job identifier")

    p_list = sub.add_parser("list", help="List recent outputs for a job")
    p_list.add_argument("job_id", help="Job identifier")
    p_list.add_argument("--limit", type=int, default=5, help="Number of entries (default 5)")

    return parser


def _print_entry(entry: dict, verbose: bool = True) -> None:
    print(f"  timestamp : {entry['timestamp']}")
    print(f"  exit_code : {entry['exit_code']}")
    if verbose:
        if entry.get("stdout"):
            print(f"  stdout    :\n{entry['stdout'].rstrip()}")
        if entry.get("stderr"):
            print(f"  stderr    :\n{entry['stderr'].rstrip()}")


def output_main(argv: list[str] | None = None) -> int:
    parser = build_output_parser()
    args = parser.parse_args(argv)

    if not args.subcmd:
        parser.print_help()
        return 1

    path = args.file or _default_path()

    if args.subcmd == "last":
        entry = last_output(path, args.job_id)
        if entry is None:
            print(f"No output recorded for job '{args.job_id}'.")
            return 0
        print(f"Last output for '{args.job_id}':")
        _print_entry(entry)
        return 0

    if args.subcmd == "list":
        entries = get_outputs(path, args.job_id, limit=args.limit)
        if not entries:
            print(f"No output recorded for job '{args.job_id}'.")
            return 0
        print(f"Output history for '{args.job_id}' ({len(entries)} entries):")
        for i, entry in enumerate(reversed(entries), 1):
            print(f"[{i}]")
            _print_entry(entry, verbose=True)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(output_main())
