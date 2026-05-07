"""CLI sub-commands for execution trace inspection."""
from __future__ import annotations

import argparse
import os
import sys

from cronwrap.trace import last_trace, load_traces, traces_for_job

_DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".cronwrap", "traces.json")


def _default_path() -> str:
    return os.environ.get("CRONWRAP_TRACE_FILE", _DEFAULT_PATH)


def _print_entry(entry: dict) -> None:
    print(f"  job_id    : {entry.get('job_id')}")
    print(f"  command   : {entry.get('command')}")
    print(f"  exit_code : {entry.get('exit_code')}")
    print(f"  duration  : {entry.get('duration')}s")
    print(f"  recorded  : {entry.get('recorded_at')}")
    tags = entry.get("tags") or {}
    if tags:
        print(f"  tags      : {tags}")
    stdout = (entry.get("stdout") or "").strip()
    if stdout:
        print(f"  stdout    : {stdout[:200]}")
    stderr = (entry.get("stderr") or "").strip()
    if stderr:
        print(f"  stderr    : {stderr[:200]}")


def build_trace_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Inspect execution traces for cron jobs."
    if parent is not None:
        parser = parent.add_parser("trace", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="cronwrap-trace", description=desc)

    parser.add_argument("--file", default=None, help="Path to trace store (default: %(default)s)")
    sub = parser.add_subparsers(dest="subcmd")

    ls = sub.add_parser("list", help="List all traces (optionally filtered by job).")
    ls.add_argument("--job", default=None, help="Filter by job_id.")

    sh = sub.add_parser("show", help="Show the last trace for a job.")
    sh.add_argument("job_id", help="Job identifier.")

    return parser


def trace_main(argv: list[str] | None = None) -> int:
    parser = build_trace_parser()
    args = parser.parse_args(argv)
    path = args.file or _default_path()

    if not args.subcmd:
        parser.print_help()
        return 1

    if args.subcmd == "list":
        if args.job:
            entries = traces_for_job(path, args.job)
        else:
            entries = load_traces(path)
        if not entries:
            print("No traces found.")
            return 0
        for entry in entries:
            print("-" * 40)
            _print_entry(entry)
        return 0

    if args.subcmd == "show":
        entry = last_trace(path, args.job_id)
        if entry is None:
            print(f"No trace found for job '{args.job_id}'.")
            return 1
        _print_entry(entry)
        return 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(trace_main())
