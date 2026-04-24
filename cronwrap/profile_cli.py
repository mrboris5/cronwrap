"""CLI sub-commands for job profiling data."""

import argparse
import sys
from typing import List, Optional

from cronwrap.profile import clear_profile, profile_stats


def _default_path() -> str:
    return "/var/lib/cronwrap/profiles.json"


def build_profile_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-profile",
        description="Inspect job timing profiles.",
    )
    parser.add_argument("--file", default=_default_path(), help="Profiles store path")
    sub = parser.add_subparsers(dest="subcmd")

    show_p = sub.add_parser("show", help="Show stats for a job")
    show_p.add_argument("job_id", help="Job identifier")

    clear_p = sub.add_parser("clear", help="Clear profile data for a job")
    clear_p.add_argument("job_id", help="Job identifier")

    return parser


def _print_stats(job_id: str, stats: dict) -> None:
    """Print formatted profile statistics for a job."""
    print(f"Job:   {job_id}")
    print(f"Count: {stats['count']}")
    print(f"Min:   {stats['min']:.4f}s")
    print(f"Max:   {stats['max']:.4f}s")
    print(f"Avg:   {stats['avg']:.4f}s")
    print(f"P95:   {stats['p95']:.4f}s")


def profile_main(argv: Optional[List[str]] = None) -> int:
    parser = build_profile_parser()
    args = parser.parse_args(argv)

    if not args.subcmd:
        parser.print_help()
        return 1

    if args.subcmd == "show":
        stats = profile_stats(args.file, args.job_id)
        if stats is None:
            print(f"No profile data for job '{args.job_id}'.")
            return 1
        _print_stats(args.job_id, stats)
        return 0

    if args.subcmd == "clear":
        removed = clear_profile(args.file, args.job_id)
        if removed:
            print(f"Cleared profile data for '{args.job_id}'.")
        else:
            print(f"No profile data found for '{args.job_id}'.")
        return 0 if removed else 1

    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(profile_main())
