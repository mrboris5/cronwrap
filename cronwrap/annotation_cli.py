"""CLI sub-commands for managing job annotations."""

import argparse
import sys
from cronwrap.annotation import (
    add_annotation,
    remove_annotation,
    get_annotations,
    clear_annotations,
    list_annotated_jobs,
)

_DEFAULT_FILE = ".cronwrap_annotations.json"


def build_annotation_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-annotation",
        description="Manage free-form notes attached to cron job IDs.",
    )
    parser.add_argument("--file", default=_DEFAULT_FILE, help="Annotations storage file.")
    sub = parser.add_subparsers(dest="subcommand")

    # add
    p_add = sub.add_parser("add", help="Attach a note to a job.")
    p_add.add_argument("job_id")
    p_add.add_argument("note", help="The annotation text.")

    # list
    p_list = sub.add_parser("list", help="Show annotations for a job.")
    p_list.add_argument("job_id")

    # remove
    p_rm = sub.add_parser("remove", help="Delete a note by index.")
    p_rm.add_argument("job_id")
    p_rm.add_argument("index", type=int, help="Zero-based index of the note to remove.")

    # clear
    p_cl = sub.add_parser("clear", help="Remove all annotations for a job.")
    p_cl.add_argument("job_id")

    # jobs
    sub.add_parser("jobs", help="List all job IDs that have annotations.")

    return parser


def annotation_main(argv=None) -> int:
    parser = build_annotation_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    f = args.file

    if args.subcommand == "add":
        try:
            notes = add_annotation(args.job_id, args.note, path=f)
            print(f"[{args.job_id}] {len(notes)} annotation(s) stored.")
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    elif args.subcommand == "list":
        notes = get_annotations(args.job_id, path=f)
        if not notes:
            print(f"No annotations for '{args.job_id}'.")
        else:
            for i, note in enumerate(notes):
                print(f"  [{i}] {note}")

    elif args.subcommand == "remove":
        try:
            notes = remove_annotation(args.job_id, args.index, path=f)
            print(f"Removed. {len(notes)} annotation(s) remaining for '{args.job_id}'.")
        except IndexError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    elif args.subcommand == "clear":
        clear_annotations(args.job_id, path=f)
        print(f"All annotations cleared for '{args.job_id}'.")

    elif args.subcommand == "jobs":
        jobs = list_annotated_jobs(path=f)
        if not jobs:
            print("No annotated jobs found.")
        else:
            for jid in jobs:
                print(f"  {jid}")

    return 0


if __name__ == "__main__":
    sys.exit(annotation_main())
