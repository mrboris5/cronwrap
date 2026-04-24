"""CLI sub-command: cronwrap trend — show job duration/success trends."""

from __future__ import annotations

import argparse
import sys

from cronwrap.metrics import load_metrics
from cronwrap.trend import duration_trend, success_trend


def _default_path() -> str:
    return "/var/lib/cronwrap/metrics.json"


def build_trend_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Show duration and success-rate trends for jobs.")
    if parent is not None:
        parser = parent.add_parser("trend", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="cronwrap-trend", **kwargs)
    parser.add_argument("--metrics-file", default=_default_path(), metavar="PATH")
    parser.add_argument(
        "job_id",
        nargs="?",
        default=None,
        help="Job ID to inspect; omit to list all jobs.",
    )
    return parser


def _print_trend(job_id: str, metrics: dict) -> None:
    dt = duration_trend(metrics)
    st = success_trend(metrics)
    dt_label = dt if dt else "n/a (insufficient data)"
    st_label = st if st else "n/a (insufficient data)"
    print(f"  job:              {job_id}")
    print(f"  duration trend:   {dt_label}")
    print(f"  success trend:    {st_label}")


def trend_main(argv: list[str] | None = None) -> int:
    parser = build_trend_parser()
    args = parser.parse_args(argv)

    all_metrics = load_metrics(args.metrics_file)
    if not all_metrics:
        print("No metrics data found.", file=sys.stderr)
        return 1

    if args.job_id:
        if args.job_id not in all_metrics:
            print(f"Job '{args.job_id}' not found in metrics.", file=sys.stderr)
            return 1
        _print_trend(args.job_id, all_metrics[args.job_id])
    else:
        for job_id, metrics in sorted(all_metrics.items()):
            _print_trend(job_id, metrics)
            print()

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(trend_main())
