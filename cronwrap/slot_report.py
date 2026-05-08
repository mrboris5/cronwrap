"""Formatting helpers for slot usage reports."""

from __future__ import annotations

from typing import Dict, List

from cronwrap.slot import load_slots, uses_in_window


def _bar(ratio: float, width: int = 20) -> str:
    filled = int(ratio * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def format_slot_entry(job_id: str, uses: List[str], max_uses: int, window: str) -> str:
    count = len(uses)
    ratio = min(count / max_uses, 1.0) if max_uses > 0 else 0.0
    bar = _bar(ratio)
    status = "EXCEEDED" if count >= max_uses else "OK"
    return (
        f"  Job     : {job_id}\n"
        f"  Uses    : {count}/{max_uses} {bar} [{status}]\n"
        f"  Window  : {window}\n"
    )


def format_slot_summary(path: str, max_uses: int, window: str) -> str:
    data = load_slots(path)
    if not data:
        return "No slot records found.\n"
    lines = ["Slot Usage Summary", "=" * 40]
    for job_id in sorted(data):
        uses = uses_in_window(path, job_id, window)
        lines.append(format_slot_entry(job_id, uses, max_uses, window))
    return "\n".join(lines) + "\n"


def print_slot_report(path: str, max_uses: int, window: str) -> None:
    print(format_slot_summary(path, max_uses, window), end="")
