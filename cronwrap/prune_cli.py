"""CLI sub-command for pruning history and audit logs using retention policies."""
from __future__ import annotations

import argparse
import sys

from cronwrap.retention import apply_retention
from cronwrap.history import load_history, save_history
from cronwrap.audit import read_audit, append_audit

import json
from pathlib import Path


def build_prune_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(description="Prune old history or audit entries")
    if parent is not None:
        parser = parent.add_parser("prune", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="cronwrap-prune", **kwargs)

    parser.add_argument("--job", required=True, help="Job ID")
    parser.add_argument("--history-file", default=None, help="Path to history JSON file")
    parser.add_argument("--audit-file", default=None, help="Path to audit JSONL file")
    parser.add_argument("--max-age", default=None, help="Max age of entries, e.g. 30d")
    parser.add_argument("--max-count", type=int, default=None, help="Max number of entries to keep")
    parser.add_argument("--dry-run", action="store_true", help="Print counts without modifying files")
    return parser


def prune_main(args: argparse.Namespace | None = None) -> int:
    parser = build_prune_parser()
    ns = parser.parse_args(namespace=args)

    if ns.max_age is None and ns.max_count is None:
        print("Error: at least one of --max-age or --max-count is required.", file=sys.stderr)
        return 1

    pruned_history = pruned_audit = 0

    if ns.history_file:
        hist = load_history(ns.history_file, ns.job)
        before = len(hist)
        hist = apply_retention(hist, max_age=ns.max_age, max_count=ns.max_count)
        pruned_history = before - len(hist)
        if not ns.dry_run:
            save_history(ns.history_file, ns.job, hist)

    if ns.audit_file:
        audit = read_audit(ns.audit_file)
        before = len(audit)
        audit = apply_retention(audit, max_age=ns.max_age, max_count=ns.max_count)
        pruned_audit = before - len(audit)
        if not ns.dry_run:
            path = Path(ns.audit_file)
            path.write_text("".join(json.dumps(e) + "\n" for e in audit))

    label = "[dry-run] Would prune" if ns.dry_run else "Pruned"
    print(f"{label}: {pruned_history} history entries, {pruned_audit} audit entries.")
    return 0


if __name__ == "__main__":
    sys.exit(prune_main())
