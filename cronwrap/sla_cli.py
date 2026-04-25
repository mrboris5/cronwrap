"""CLI for inspecting SLA records."""

import argparse
import sys
from cronwrap.sla import load_sla_records, sla_summary

DEFAULT_PATH = "/var/lib/cronwrap/sla.json"


def _default_path() -> str:
    return DEFAULT_PATH


def build_sla_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-sla", description="SLA record management")
    p.add_argument("--file", default=_default_path(), help="SLA records file")
    sub = p.add_subparsers(dest="subcommand")

    show = sub.add_parser("show", help="Show SLA summary for a job")
    show.add_argument("job_id", help="Job identifier")

    ls = sub.add_parser("list", help="List all jobs with SLA data")
    ls.add_argument("--min-violations", type=int, default=0,
                    help="Only show jobs with at least N violations")

    hist = sub.add_parser("history", help="Show recent run history for a job")
    hist.add_argument("job_id", help="Job identifier")
    hist.add_argument("--limit", type=int, default=10, help="Number of entries")

    return p


def _print_summary(summary: dict) -> None:
    print(f"Job:         {summary['job_id']}")
    print(f"Total runs:  {summary['total']}")
    print(f"Violations:  {summary['violations']}")
    print(f"Compliance:  {summary['compliance'] * 100:.1f}%")
    print(f"Last run:    {summary['last_run'] or 'never'}")


def sla_main(argv=None) -> int:
    parser = build_sla_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "show":
        summary = sla_summary(args.file, args.job_id)
        _print_summary(summary)
        return 0

    if args.subcommand == "list":
        records = load_sla_records(args.file)
        if not records:
            print("No SLA records found.")
            return 0
        for job_id, entry in sorted(records.items()):
            violations = entry.get("violations", 0)
            if violations >= args.min_violations:
                total = entry.get("total", 0)
                rate = (1.0 - violations / total) * 100 if total else 100.0
                print(f"{job_id:<30} runs={total:<6} violations={violations:<6} compliance={rate:.1f}%")
        return 0

    if args.subcommand == "history":
        records = load_sla_records(args.file)
        entry = records.get(args.job_id)
        if not entry:
            print(f"No records for job '{args.job_id}'.")
            return 1
        history = entry.get("history", [])[-args.limit:]
        for run in history:
            status = "OK" if run["success"] else "FAIL"
            breach = " [BREACH]" if run["breached"] else ""
            print(f"{run['timestamp']}  {status:<4}  {run['duration']:.3f}s{breach}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(sla_main())
