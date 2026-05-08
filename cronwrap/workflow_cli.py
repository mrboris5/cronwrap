"""CLI for managing workflow definitions."""
from __future__ import annotations

import argparse
import sys

from cronwrap.workflow import (
    register_workflow, get_workflow, remove_workflow, list_workflows
)

_DEFAULT_PATH = "/var/lib/cronwrap/workflows.json"


def build_workflow_parser(default_path: str = _DEFAULT_PATH) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwrap-workflow",
                                description="Manage job workflows")
    p.add_argument("--file", default=default_path, metavar="PATH")
    sub = p.add_subparsers(dest="subcommand")

    reg = sub.add_parser("register", help="Register a workflow")
    reg.add_argument("workflow_id")
    reg.add_argument("steps", nargs="+", help="Ordered job IDs")
    reg.add_argument("--description", default="")

    show = sub.add_parser("show", help="Show a workflow")
    show.add_argument("workflow_id")

    rm = sub.add_parser("remove", help="Remove a workflow")
    rm.add_argument("workflow_id")

    sub.add_parser("list", help="List all workflows")
    return p


def _print_workflow(wf: dict) -> None:
    print(f"id:          {wf['workflow_id']}")
    print(f"description: {wf.get('description', '')}")
    print(f"steps:       {' -> '.join(wf.get('steps', []))}")


def workflow_main(argv=None) -> int:
    parser = build_workflow_parser()
    args = parser.parse_args(argv)
    if not args.subcommand:
        parser.print_help()
        return 1

    if args.subcommand == "register":
        wf = register_workflow(args.file, args.workflow_id,
                               args.steps, args.description)
        print(f"Registered workflow '{wf['workflow_id']}' "
              f"with {len(wf['steps'])} step(s).")
        return 0

    if args.subcommand == "show":
        wf = get_workflow(args.file, args.workflow_id)
        if wf is None:
            print(f"Workflow '{args.workflow_id}' not found.", file=sys.stderr)
            return 1
        _print_workflow(wf)
        return 0

    if args.subcommand == "remove":
        ok = remove_workflow(args.file, args.workflow_id)
        if not ok:
            print(f"Workflow '{args.workflow_id}' not found.", file=sys.stderr)
            return 1
        print(f"Removed workflow '{args.workflow_id}'.")
        return 0

    if args.subcommand == "list":
        workflows = list_workflows(args.file)
        if not workflows:
            print("No workflows registered.")
            return 0
        for wf in workflows:
            _print_workflow(wf)
            print()
        return 0

    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(workflow_main())
