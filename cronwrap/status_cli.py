"""CLI for inspecting job status."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwrap.status import all_statuses, get_status, _DEFAULT_PATH

_STATE_SYMBOLS = {"ok": "\u2705", "degraded": "\u26a0\ufe0f", "failing": "\u274c", "unknown": "\u2753"}


def _print_entry(entry: dict) -> None:
    sym = _STATE_SYMBOLS.get(entry.get("state", "unknown"), "?")
    print(
        f"{sym}  {entry['job_id']:30s}  "
        f"state={entry.get('state','unknown'):10s}  "
        f"failures={entry.get('consecutive_failures', 0)}  "
        f"last_run={entry.get('last_run') or 'never'}"
    )


def build_status_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-status", description="Show job status")
    p.add_argument("--file", default=str(_DEFAULT_PATH), help="Status file path")
    sub = p.add_subparsers(dest="cmd")

    ls = sub.add_parser("list", help="List all job statuses")
    ls.add_argument("--state", choices=["ok", "degraded", "failing", "unknown"], help="Filter by state")

    show = sub.add_parser("show", help="Show status for a specific job")
    show.add_argument("job_id", help="Job identifier")

    return p


def status_main(argv=None) -> int:
    parser = build_status_parser()
    args = parser.parse_args(argv)
    path = Path(args.file)

    if args.cmd == "list":
        entries = all_statuses(path)
        if args.state:
            entries = [e for e in entries if e.get("state") == args.state]
        if not entries:
            print("No status records found.")
            return 0
        for e in sorted(entries, key=lambda x: x["job_id"]):
            _print_entry(e)
        return 0

    if args.cmd == "show":
        entry = get_status(args.job_id, path)
        if entry is None:
            print(f"No status for job '{args.job_id}'.")
            return 1
        _print_entry(entry)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(status_main())
