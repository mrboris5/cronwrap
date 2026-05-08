"""CLI for inspecting and managing token buckets."""

from __future__ import annotations

import argparse
import sys

from cronwrap.token import available_tokens, consume_token, reset_tokens, load_tokens

_DEFAULT_PATH = "/var/lib/cronwrap/tokens.json"


def _default_path() -> str:
    return _DEFAULT_PATH


def build_token_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-token", description="Token bucket management")
    p.add_argument("--file", default=_default_path(), help="Token store path")
    sub = p.add_subparsers(dest="cmd")

    sh = sub.add_parser("show", help="Show available tokens for a job")
    sh.add_argument("job_id")
    sh.add_argument("--rate", type=float, default=1.0)
    sh.add_argument("--capacity", type=float, default=10.0)

    co = sub.add_parser("consume", help="Consume one token for a job")
    co.add_argument("job_id")
    co.add_argument("--rate", type=float, default=1.0)
    co.add_argument("--capacity", type=float, default=10.0)

    rs = sub.add_parser("reset", help="Reset tokens for a job to full capacity")
    rs.add_argument("job_id")
    rs.add_argument("--capacity", type=float, default=10.0)

    sub.add_parser("list", help="List all token bucket entries")

    return p


def token_main(argv=None) -> int:
    parser = build_token_parser()
    args = parser.parse_args(argv)

    if not args.cmd:
        parser.print_help()
        return 1

    if args.cmd == "show":
        t = available_tokens(args.file, args.job_id, args.rate, args.capacity)
        print(f"{args.job_id}: {t:.4f} tokens available")

    elif args.cmd == "consume":
        ok = consume_token(args.file, args.job_id, args.rate, args.capacity)
        if ok:
            print(f"Token consumed for {args.job_id}")
        else:
            print(f"No tokens available for {args.job_id}", file=sys.stderr)
            return 2

    elif args.cmd == "reset":
        reset_tokens(args.file, args.job_id, args.capacity)
        print(f"Tokens reset for {args.job_id}")

    elif args.cmd == "list":
        data = load_tokens(args.file)
        if not data:
            print("No token entries found.")
        else:
            for job_id, entry in sorted(data.items()):
                print(f"{job_id}: tokens={entry.get('tokens', '?'):.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(token_main())
