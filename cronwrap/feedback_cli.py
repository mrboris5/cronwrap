"""CLI interface for the feedback module."""
from __future__ import annotations

import argparse
import sys

from cronwrap.feedback import (
    add_feedback,
    average_rating,
    get_feedback,
    remove_feedback,
)

_DEFAULT_PATH = "/var/lib/cronwrap/feedback.json"


def _print_entries(entries: list) -> None:
    if not entries:
        print("  (no feedback)")
        return
    for e in entries:
        stars = "*" * e["rating"]
        author = f" [{e['author']}]" if e.get("author") else ""
        print(f"  {e['timestamp']}{author}  {stars}  {e['comment']}")


def build_feedback_parser(default_path: str = _DEFAULT_PATH) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-feedback", description="Manage job run feedback")
    p.add_argument("--file", default=default_path, metavar="PATH")
    sub = p.add_subparsers(dest="subcmd")

    add_p = sub.add_parser("add", help="Add feedback for a run")
    add_p.add_argument("job_id")
    add_p.add_argument("run_id")
    add_p.add_argument("rating", type=int, choices=range(1, 6), metavar="RATING (1-5)")
    add_p.add_argument("--comment", default="")
    add_p.add_argument("--author", default="")

    show_p = sub.add_parser("show", help="Show feedback for a job")
    show_p.add_argument("job_id")

    avg_p = sub.add_parser("avg", help="Show average rating for a job")
    avg_p.add_argument("job_id")

    rm_p = sub.add_parser("remove", help="Remove feedback for a run")
    rm_p.add_argument("job_id")
    rm_p.add_argument("run_id")

    return p


def feedback_main(argv: list[str] | None = None) -> int:
    parser = build_feedback_parser()
    args = parser.parse_args(argv)

    if not args.subcmd:
        parser.print_help()
        return 1

    if args.subcmd == "add":
        entry = add_feedback(
            args.file, args.job_id, args.run_id, args.rating,
            comment=args.comment, author=args.author,
        )
        print(f"Feedback recorded: rating={entry['rating']} at {entry['timestamp']}")

    elif args.subcmd == "show":
        entries = get_feedback(args.file, args.job_id)
        print(f"Feedback for {args.job_id}:")
        _print_entries(entries)

    elif args.subcmd == "avg":
        avg = average_rating(args.file, args.job_id)
        if avg is None:
            print(f"No feedback for {args.job_id}")
        else:
            print(f"Average rating for {args.job_id}: {avg:.2f}")

    elif args.subcmd == "remove":
        removed = remove_feedback(args.file, args.job_id, args.run_id)
        if removed:
            print(f"Removed feedback for run {args.run_id}")
        else:
            print(f"No feedback found for run {args.run_id}")
            return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(feedback_main())
