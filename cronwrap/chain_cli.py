"""CLI interface for managing job chains."""

import argparse
import sys
from cronwrap.chain import (
    load_chains,
    register_chain,
    get_chain,
    remove_chain,
    advance_chain,
    current_step,
)

_DEFAULT_PATH = "/var/lib/cronwrap/chains.json"


def _default_path() -> str:
    return _DEFAULT_PATH


def _print_chain(entry: dict) -> None:
    print(f"chain_id : {entry['chain_id']}")
    print(f"status   : {entry['status']}")
    print(f"steps    : {', '.join(entry['steps'])}")
    step = current_step(entry)
    print(f"current  : {step if step else '(complete)'}")
    if entry.get("description"):
        print(f"desc     : {entry['description']}")


def build_chain_parser(default_path: str = _DEFAULT_PATH) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-chain", description="Manage job chains")
    p.add_argument("--file", default=default_path, help="Path to chains JSON file")
    sub = p.add_subparsers(dest="cmd")

    reg = sub.add_parser("register", help="Register a new chain")
    reg.add_argument("chain_id")
    reg.add_argument("steps", nargs="+", help="Ordered job IDs")
    reg.add_argument("--description", default="")

    show = sub.add_parser("show", help="Show a chain")
    show.add_argument("chain_id")

    ls = sub.add_parser("list", help="List all chains")  # noqa: F841

    adv = sub.add_parser("advance", help="Advance a chain to the next step")
    adv.add_argument("chain_id")

    rm = sub.add_parser("remove", help="Remove a chain")
    rm.add_argument("chain_id")

    return p


def chain_main(argv=None, default_path: str = _DEFAULT_PATH) -> int:
    parser = build_chain_parser(default_path)
    args = parser.parse_args(argv)

    if not args.cmd:
        parser.print_help()
        return 1

    if args.cmd == "register":
        entry = register_chain(args.file, args.chain_id, args.steps, args.description)
        print(f"Registered chain '{args.chain_id}' with {len(entry['steps'])} step(s).")
        return 0

    if args.cmd == "show":
        entry = get_chain(args.file, args.chain_id)
        if entry is None:
            print(f"Chain not found: {args.chain_id}", file=sys.stderr)
            return 2
        _print_chain(entry)
        return 0

    if args.cmd == "list":
        chains = load_chains(args.file)
        if not chains:
            print("No chains registered.")
        for cid, entry in sorted(chains.items()):
            step = current_step(entry)
            print(f"{cid:30s}  {entry['status']:10s}  {step or '(complete)'}")
        return 0

    if args.cmd == "advance":
        try:
            entry = advance_chain(args.file, args.chain_id)
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        step = current_step(entry)
        print(f"Advanced '{args.chain_id}': status={entry['status']}, next={step or '(complete)'}")
        return 0

    if args.cmd == "remove":
        removed = remove_chain(args.file, args.chain_id)
        if not removed:
            print(f"Chain not found: {args.chain_id}", file=sys.stderr)
            return 2
        print(f"Removed chain '{args.chain_id}'.")
        return 0

    return 1
