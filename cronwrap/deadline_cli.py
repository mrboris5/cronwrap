"""CLI sub-tool for checking job deadlines."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Optional

from cronwrap.deadline import check_deadline


def _parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 datetime string into a timezone-aware datetime."""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid ISO datetime: {value!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def build_deadline_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-deadline",
        description="Check whether a job has missed its start deadline.",
    )
    sub = parser.add_subparsers(dest="subcommand")

    check = sub.add_parser("check", help="Check if a job is past its deadline.")
    check.add_argument("--job", required=True, help="Job identifier.")
    check.add_argument(
        "--scheduled-at",
        required=True,
        type=_parse_iso,
        metavar="ISO_DATETIME",
        help="When the job was scheduled (ISO-8601, UTC assumed if no tz).",
    )
    check.add_argument(
        "--deadline",
        required=True,
        metavar="DURATION",
        help="Max allowed delay, e.g. '5m', '1h', '30s'.",
    )

    return parser


def deadline_main(argv: Optional[list[str]] = None) -> int:
    parser = build_deadline_parser()
    args = parser.parse_args(argv)

    if args.subcommand is None:
        parser.print_help()
        return 1

    if args.subcommand == "check":
        blocked, reason = check_deadline(
            job_id=args.job,
            scheduled_at=args.scheduled_at,
            deadline=args.deadline,
        )
        if blocked:
            print(f"BLOCKED: {reason}", file=sys.stderr)
            return 2
        print(
            f"OK: job '{args.job}' is within its deadline of {args.deadline}."
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(deadline_main())
