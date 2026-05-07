"""CLI interface for managing alert rules."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from cronwrap.alert_rule import (
    evaluate_rule,
    get_alert_rule,
    list_rules,
    remove_alert_rule,
    set_alert_rule,
)

_DEFAULT_PATH = "/var/lib/cronwrap/alert_rules.json"


def _default_path() -> str:
    return _DEFAULT_PATH


def build_alert_rule_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-alert-rule", description="Manage alert rules")
    p.add_argument("--file", default=_default_path(), help="Path to alert rules file")
    sub = p.add_subparsers(dest="subcommand")

    s = sub.add_parser("set", help="Set an alert rule")
    s.add_argument("job_id")
    s.add_argument("condition", choices=["gt", "lt", "gte", "lte", "eq"])
    s.add_argument("threshold", type=float)
    s.add_argument("--channel", default="email")
    s.add_argument("--disabled", action="store_true")

    g = sub.add_parser("get", help="Get an alert rule")
    g.add_argument("job_id")

    r = sub.add_parser("remove", help="Remove an alert rule")
    r.add_argument("job_id")

    sub.add_parser("list", help="List all alert rules")

    e = sub.add_parser("eval", help="Evaluate a rule against a value")
    e.add_argument("job_id")
    e.add_argument("value", type=float)

    return p


def alert_rule_main(argv: Optional[List[str]] = None) -> int:
    parser = build_alert_rule_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "set":
        entry = set_alert_rule(
            args.file,
            args.job_id,
            args.condition,
            args.threshold,
            channel=args.channel,
            enabled=not args.disabled,
        )
        print(f"Rule set for {args.job_id}: {entry}")
        return 0

    if args.subcommand == "get":
        rule = get_alert_rule(args.file, args.job_id)
        if rule is None:
            print(f"No rule for {args.job_id}", file=sys.stderr)
            return 1
        print(rule)
        return 0

    if args.subcommand == "remove":
        removed = remove_alert_rule(args.file, args.job_id)
        if not removed:
            print(f"No rule for {args.job_id}", file=sys.stderr)
            return 1
        print(f"Removed rule for {args.job_id}")
        return 0

    if args.subcommand == "list":
        for entry in list_rules(args.file):
            print(entry)
        return 0

    if args.subcommand == "eval":
        rule = get_alert_rule(args.file, args.job_id)
        if rule is None:
            print(f"No rule for {args.job_id}", file=sys.stderr)
            return 1
        triggered = evaluate_rule(rule, args.value)
        print("TRIGGERED" if triggered else "OK")
        return 0

    return 1
