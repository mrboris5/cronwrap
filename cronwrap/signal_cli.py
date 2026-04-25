"""CLI sub-commands for signal / shutdown inspection."""

import argparse
import sys
import os
import signal


def build_signal_parser(parent: argparse.ArgumentParser = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="cronwrap-signal",
        description="Send a signal to a running cronwrap process.",
    )
    sub = parser.add_subparsers(dest="signal_cmd")

    send = sub.add_parser("send", help="Send a signal to a PID")
    send.add_argument("pid", type=int, help="Target process ID")
    send.add_argument(
        "--sig",
        default="SIGTERM",
        choices=["SIGTERM", "SIGINT", "SIGHUP"],
        help="Signal name (default: SIGTERM)",
    )

    sub.add_parser("list", help="List supported signals")
    return parser


def _send(args: argparse.Namespace) -> int:
    try:
        sig = signal.Signals[args.sig]
    except KeyError:
        print(f"Unknown signal: {args.sig}", file=sys.stderr)
        return 1
    try:
        os.kill(args.pid, sig)
        print(f"Sent {args.sig} to PID {args.pid}")
        return 0
    except ProcessLookupError:
        print(f"No process with PID {args.pid}", file=sys.stderr)
        return 2
    except PermissionError:
        print(f"Permission denied sending to PID {args.pid}", file=sys.stderr)
        return 3


def signal_main(argv=None) -> int:
    parser = build_signal_parser()
    args = parser.parse_args(argv)

    if args.signal_cmd == "send":
        return _send(args)
    if args.signal_cmd == "list":
        for name in ("SIGTERM", "SIGINT", "SIGHUP"):
            print(name)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(signal_main())
