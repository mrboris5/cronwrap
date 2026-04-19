"""CLI commands for inspecting and managing job checkpoints."""
from __future__ import annotations

import argparse
import json
import sys

from cronwrap.checkpoint import (
    get_checkpoint,
    set_checkpoint,
    clear_checkpoint,
    clear_all_checkpoints,
    load_checkpoints,
)

DEFAULT_FILE = "/var/lib/cronwrap/checkpoints.json"


def build_checkpoint_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-checkpoint", description="Manage job checkpoints")
    p.add_argument("--file", default=DEFAULT_FILE, help="Checkpoint storage file")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("list", help="List all checkpoints")

    g = sub.add_parser("get", help="Get checkpoint for a job")
    g.add_argument("job_id")

    s = sub.add_parser("set", help="Set checkpoint for a job")
    s.add_argument("job_id")
    s.add_argument("value")

    c = sub.add_parser("clear", help="Clear checkpoint for a job")
    c.add_argument("job_id")

    sub.add_parser("clear-all", help="Clear all checkpoints")

    return p


def checkpoint_main(argv: list[str] | None = None) -> int:
    parser = build_checkpoint_parser()
    args = parser.parse_args(argv)

    if args.cmd == "list":
        data = load_checkpoints(args.file)
        if not data:
            print("No checkpoints stored.")
        else:
            for job_id, value in sorted(data.items()):
                print(f"{job_id}\t{json.dumps(value)}")

    elif args.cmd == "get":
        val = get_checkpoint(args.file, args.job_id)
        if val is None:
            print(f"No checkpoint for {args.job_id!r}")
            return 1
        print(json.dumps(val))

    elif args.cmd == "set":
        set_checkpoint(args.file, args.job_id, args.value)
        print(f"Checkpoint set: {args.job_id} = {args.value!r}")

    elif args.cmd == "clear":
        removed = clear_checkpoint(args.file, args.job_id)
        if removed:
            print(f"Cleared checkpoint for {args.job_id!r}")
        else:
            print(f"No checkpoint found for {args.job_id!r}")
            return 1

    elif args.cmd == "clear-all":
        count = clear_all_checkpoints(args.file)
        print(f"Cleared {count} checkpoint(s).")

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(checkpoint_main())
