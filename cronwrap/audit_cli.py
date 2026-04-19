"""CLI helpers for querying the audit log."""

import argparse
import sys
from typing import List, Optional

from cronwrap.audit import read_audit


def _print_entries(entries: list, verbose: bool = False) -> None:
    if not entries:
        print("No audit entries found.")
        return
    for e in entries:
        status = "OK" if e.get("exit_code", 1) == 0 else "FAIL"
        line = f"{e.get('ts', '?')}  [{status}]  {e.get('job_id', '?')}  {e.get('command', '?')}  ({e.get('duration', 0):.3f}s)"
        if verbose and e.get("note"):
            line += f"  note={e['note']}"
        if verbose and e.get("tags"):
            tags_str = ",".join(f"{k}={v}" for k, v in e["tags"].items())
            line += f"  tags={tags_str}"
        print(line)


def build_audit_parser(sub=None) -> argparse.ArgumentParser:
    if sub is not None:
        p = sub.add_parser("audit", help="Query the audit log")
    else:
        p = argparse.ArgumentParser(description="Query cronwrap audit log")
    p.add_argument("--file", default="cronwrap_audit.jsonl", help="Audit log file")
    p.add_argument("--job", default=None, help="Filter by job ID")
    p.add_argument("--tail", type=int, default=0, help="Show last N entries")
    p.add_argument("--verbose", action="store_true", help="Show tags and notes")
    return p


def audit_main(argv: Optional[List[str]] = None) -> int:
    parser = build_audit_parser()
    args = parser.parse_args(argv)

    entries = read_audit(args.file, job_id=args.job)

    if args.tail > 0:
        entries = entries[-args.tail:]

    _print_entries(entries, verbose=args.verbose)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(audit_main())
