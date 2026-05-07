"""Formatting helpers for job notes."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from cronwrap.note import load_notes


def format_note_entry(job_id: str, notes: List[str]) -> str:
    """Return a formatted block for one job's notes."""
    if not notes:
        return f"{job_id}: (no notes)"
    lines = [f"{job_id}:"]
    for i, text in enumerate(notes):
        lines.append(f"  [{i}] {text}")
    return "\n".join(lines)


def format_note_summary(notes: Dict[str, List[str]]) -> str:
    """Return a multi-job summary string."""
    if not notes:
        return "No notes recorded."
    blocks = [format_note_entry(jid, txts) for jid, txts in sorted(notes.items())]
    total = sum(len(v) for v in notes.values())
    blocks.append(f"\nTotal notes: {total} across {len(notes)} job(s).")
    return "\n".join(blocks)


def print_note_report(path: Path) -> None:
    """Print a full notes report to stdout."""
    notes = load_notes(path)
    print(format_note_summary(notes))
