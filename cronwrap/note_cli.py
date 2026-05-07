"""CLI sub-commands for managing per-job notes."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwrap.note import add_note, clear_notes, get_notes, remove_note

_DEFAULT_PATH = Path(".cronwrap") / "notes.json"


def build_note_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-note", description="Manage job notes")
    p.add_argument("--file", type=Path, default=_DEFAULT_PATH, metavar="PATH")
    sub = p.add_subparsers(dest="cmd")

    add_p = sub.add_parser("add", help="Add a note to a job")
    add_p.add_argument("job_id")
    add_p.add_argument("text")

    ls_p = sub.add_parser("list", help="List notes for a job")
    ls_p.add_argument("job_id")

    rm_p = sub.add_parser("remove", help="Remove a note by index")
    rm_p.add_argument("job_id")
    rm_p.add_argument("index", type=int)

    clr_p = sub.add_parser("clear", help="Clear all notes for a job")
    clr_p.add_argument("job_id")

    return p


def note_main(argv: list[str] | None = None) -> int:
    parser = build_note_parser()
    args = parser.parse_args(argv)

    if not args.cmd:
        parser.print_help()
        return 1

    if args.cmd == "add":
        notes = add_note(args.job_id, args.text, path=args.file)
        print(f"Note added. {len(notes)} note(s) for '{args.job_id}'.")

    elif args.cmd == "list":
        notes = get_notes(args.job_id, path=args.file)
        if not notes:
            print(f"No notes for '{args.job_id}'.")
        else:
            for i, text in enumerate(notes):
                print(f"  [{i}] {text}")

    elif args.cmd == "remove":
        removed = remove_note(args.job_id, args.index, path=args.file)
        if removed is None:
            print(f"Index {args.index} out of range for '{args.job_id}'.", file=sys.stderr)
            return 1
        print(f"Removed: {removed}")

    elif args.cmd == "clear":
        count = clear_notes(args.job_id, path=args.file)
        print(f"Cleared {count} note(s) for '{args.job_id}'.")

    return 0


if __name__ == "__main__":
    sys.exit(note_main())
