"""CLI sub-commands for managing job pauses."""

from __future__ import annotations

import argparse
import sys

from cronwrap.pause import (
    _DEFAULT_FILE,
    is_paused,
    load_paused,
    pause_job,
    resume_job,
)


def build_pause_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-pause",
        description="Pause or resume cronwrap jobs.",
    )
    parser.add_argument(
        "--file",
        default=_DEFAULT_FILE,
        help="Path to the paused-jobs store (default: %(default)s)",
    )
    sub = parser.add_subparsers(dest="command")

    # pause
    p_pause = sub.add_parser("pause", help="Pause a job.")
    p_pause.add_argument("job_id", help="Job identifier to pause.")
    p_pause.add_argument(
        "--expires",
        default=None,
        metavar="ISO8601",
        help="Optional expiry datetime (ISO-8601) after which the pause lifts.",
    )

    # resume
    p_resume = sub.add_parser("resume", help="Resume a paused job.")
    p_resume.add_argument("job_id", help="Job identifier to resume.")

    # status
    p_status = sub.add_parser("status", help="Show pause status for a job.")
    p_status.add_argument("job_id", help="Job identifier to query.")

    # list
    sub.add_parser("list", help="List all currently paused jobs.")

    return parser


def pause_main(argv: list[str] | None = None) -> int:
    parser = build_pause_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "pause":
        entry = pause_job(args.job_id, expires=args.expires, path=args.file)
        print(f"Paused '{args.job_id}' at {entry['paused_at']}", end="")
        if entry["expires"]:
            print(f" (expires {entry['expires']})", end="")
        print()
        return 0

    if args.command == "resume":
        removed = resume_job(args.job_id, path=args.file)
        if removed:
            print(f"Resumed '{args.job_id}'.")
            return 0
        print(f"'{args.job_id}' was not paused.", file=sys.stderr)
        return 1

    if args.command == "status":
        paused = is_paused(args.job_id, path=args.file)
        state = "paused" if paused else "active"
        print(f"{args.job_id}: {state}")
        return 0

    if args.command == "list":
        data = load_paused(path=args.file)
        if not data:
            print("No jobs are currently paused.")
            return 0
        for jid, entry in data.items():
            expires = entry.get("expires") or "never"
            print(f"  {jid}  paused_at={entry['paused_at']}  expires={expires}")
        return 0

    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pause_main())
