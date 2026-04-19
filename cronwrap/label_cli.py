"""CLI sub-commands for managing job labels."""
from __future__ import annotations
import argparse
import sys
from cronwrap.label import add_label, remove_label, get_labels, jobs_with_label, clear_labels

_DEFAULT_FILE = ".cronwrap_labels.json"


def build_label_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    desc = "Manage labels attached to cron job IDs"
    if parent:
        p = parent.add_parser("label", help=desc)
    else:
        p = argparse.ArgumentParser(prog="cronwrap-label", description=desc)
    p.add_argument("--file", default=_DEFAULT_FILE, help="Labels JSON file")
    sub = p.add_subparsers(dest="label_cmd")

    add_p = sub.add_parser("add", help="Add a label to a job")
    add_p.add_argument("job_id")
    add_p.add_argument("label")

    rm_p = sub.add_parser("remove", help="Remove a label from a job")
    rm_p.add_argument("job_id")
    rm_p.add_argument("label")

    ls_p = sub.add_parser("list", help="List labels for a job")
    ls_p.add_argument("job_id")

    find_p = sub.add_parser("find", help="Find jobs with a given label")
    find_p.add_argument("label")

    clr_p = sub.add_parser("clear", help="Clear all labels for a job")
    clr_p.add_argument("job_id")

    return p


def label_main(argv: list[str] | None = None) -> int:
    parser = build_label_parser()
    args = parser.parse_args(argv)
    f = args.file

    if args.label_cmd == "add":
        labels = add_label(args.job_id, args.label, f)
        print(f"{args.job_id}: {labels}")
    elif args.label_cmd == "remove":
        labels = remove_label(args.job_id, args.label, f)
        print(f"{args.job_id}: {labels}")
    elif args.label_cmd == "list":
        labels = get_labels(args.job_id, f)
        print("\n".join(labels) if labels else "(no labels)")
    elif args.label_cmd == "find":
        jobs = jobs_with_label(args.label, f)
        print("\n".join(jobs) if jobs else "(none)")
    elif args.label_cmd == "clear":
        clear_labels(args.job_id, f)
        print(f"Cleared labels for {args.job_id}")
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(label_main())
