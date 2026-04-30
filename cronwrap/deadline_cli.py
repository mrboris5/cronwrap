"""CLI sub-tool for checking job deadlines."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Optional

from cronwrap.deadline import check_deadline


def _parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 datetime string into a timezone-aware datetime.

    If the string has no timezone information, UTC is assumed.

    Args:
        value: An ISO-8601 formatted datetime string.

    Returns:
        A timezone-aware :class:`datetime` object.

    Raises:
        argparse.ArgumentTypeError: If *value* cannot be parsed as ISO-8601.
    """
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid ISO datetime: {value!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def build_deadline_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the deadline sub-tool."""
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


def _handle_check(args: argparse.Namespace) -> int:
    """Execute the 'check' subcommand and return an exit code.

    Calls :func:`cronwrap.deadline.check_deadline` with the parsed arguments
    and prints a human-readable result to stdout or stderr.

    Args:
        args: Parsed namespace containing ``job``, ``scheduled_at``, and
              ``deadline`` attributes.

    Returns:
        ``0`` if the job is within its deadline, ``2`` if it has been blocked.
    """
    blocked, reason = check_deadline(
        job_id=args.job,
        scheduled_at=args.scheduled_at,
        deadline=args.deadline,
    )
    if blocked:
        print(f"BLOCKED: {reason}", file=sys.stderr)
        return 2
    print(f"OK: job '{args.job}' is within its deadline of {args.deadline}.")
    return 0


def deadline_main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the cronwrap-deadline command-line tool.

    Args:
        argv: Argument list to parse; defaults to ``sys.argv[1:]`` when
              *None*.

    Returns:
        An integer exit code suitable for passing to :func:`sys.exit`.
    """
    parser = build_deadline_parser()
    args = parser.parse_args(argv)

    if args.subcommand is None:
        parser.print_help()
        return 1

    if args.subcommand == "check":
        return _handle_check(args)

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(deadline_main())
