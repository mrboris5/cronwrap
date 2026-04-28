"""CLI sub-commands for job lineage inspection."""
from __future__ import annotations

import argparse
import sys
from typing import List

from cronwrap.lineage import find_children, get_lineage, lineage_summary, record_lineage

_DEFAULT_PATH = "/var/lib/cronwrap/lineage.json"


def _print_entries(entries: List[dict]) -> None:
    if not entries:
        print("(no entries)")
        return
    for e in entries:
        parts = [f"run_id={e.get('run_id', '?')}"]
        if "parent_run_id" in e:
            parts.append(f"parent={e['parent_run_id']}")
        if "triggered_by" in e:
            parts.append(f"triggered_by={e['triggered_by']}")
        if "job_id" in e:
            parts.insert(0, f"job={e['job_id']}")
        print("  ", "  ".join(parts))


def build_lineage_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-lineage", description="Manage job lineage")
    p.add_argument("--file", default=_DEFAULT_PATH, help="Lineage store path")
    sub = p.add_subparsers(dest="cmd")

    rec = sub.add_parser("record", help="Record a lineage entry")
    rec.add_argument("job_id")
    rec.add_argument("run_id")
    rec.add_argument("--parent", dest="parent_run_id", default=None)
    rec.add_argument("--triggered-by", dest="triggered_by", default=None)

    show = sub.add_parser("show", help="Show lineage for a job")
    show.add_argument("job_id")

    children = sub.add_parser("children", help="Show child runs of a given run_id")
    children.add_argument("parent_run_id")

    summ = sub.add_parser("summary", help="Print lineage summary for a job")
    summ.add_argument("job_id")

    return p


def lineage_main(argv: List[str] | None = None) -> int:
    parser = build_lineage_parser()
    args = parser.parse_args(argv)

    if args.cmd is None:
        parser.print_help()
        return 1

    if args.cmd == "record":
        entry = record_lineage(
            args.file,
            args.job_id,
            args.run_id,
            parent_run_id=args.parent_run_id,
            triggered_by=args.triggered_by,
        )
        print("Recorded:", entry)

    elif args.cmd == "show":
        entries = get_lineage(args.file, args.job_id)
        _print_entries(entries)

    elif args.cmd == "children":
        entries = find_children(args.file, args.parent_run_id)
        _print_entries(entries)

    elif args.cmd == "summary":
        print(lineage_summary(args.file, args.job_id))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(lineage_main())
