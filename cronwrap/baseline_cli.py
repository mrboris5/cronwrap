"""CLI sub-commands for managing job duration baselines."""

import argparse
import sys

from cronwrap.baseline import (
    DEFAULT_PATH,
    get_baseline,
    load_baselines,
    remove_baseline,
    set_baseline,
)


def build_baseline_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap-baseline",
        description="Manage expected-duration baselines for cron jobs",
    )
    parser.add_argument("--file", default=DEFAULT_PATH, help="Baselines file path")
    sub = parser.add_subparsers(dest="subcommand")

    # set
    p_set = sub.add_parser("set", help="Set baseline for a job")
    p_set.add_argument("job_id")
    p_set.add_argument("seconds", type=float, help="Expected duration in seconds")

    # get
    p_get = sub.add_parser("get", help="Get baseline for a job")
    p_get.add_argument("job_id")

    # remove
    p_rm = sub.add_parser("remove", help="Remove baseline for a job")
    p_rm.add_argument("job_id")

    # list
    sub.add_parser("list", help="List all baselines")

    return parser


def baseline_main(argv=None) -> int:
    parser = build_baseline_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "set":
        try:
            entry = set_baseline(args.job_id, args.seconds, path=args.file)
            print(f"Baseline set: {args.job_id} = {entry['expected_seconds']}s")
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

    elif args.subcommand == "get":
        val = get_baseline(args.job_id, path=args.file)
        if val is None:
            print(f"No baseline for '{args.job_id}'")
            return 1
        print(f"{args.job_id}: {val}s")

    elif args.subcommand == "remove":
        removed = remove_baseline(args.job_id, path=args.file)
        if not removed:
            print(f"No baseline found for '{args.job_id}'", file=sys.stderr)
            return 1
        print(f"Baseline removed: {args.job_id}")

    elif args.subcommand == "list":
        data = load_baselines(path=args.file)
        if not data:
            print("No baselines recorded.")
        else:
            for jid, entry in sorted(data.items()):
                print(f"{jid}: {entry['expected_seconds']}s")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(baseline_main())
