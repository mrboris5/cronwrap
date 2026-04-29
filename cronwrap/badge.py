"""Badge generation for job status — produces shields.io-compatible JSON badges."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cronwrap.metrics import load_metrics

_COLOR_MAP = {
    "passing": "brightgreen",
    "failing": "red",
    "degraded": "yellow",
    "unknown": "lightgrey",
}


def _status_for(success_rate: float | None) -> str:
    if success_rate is None:
        return "unknown"
    if success_rate >= 0.95:
        return "passing"
    if success_rate >= 0.75:
        return "degraded"
    return "failing"


def build_badge(job_id: str, metrics_path: str) -> dict[str, Any]:
    """Return a shields.io endpoint-compatible badge dict for *job_id*."""
    metrics = load_metrics(metrics_path)
    entry = metrics.get(job_id)

    if entry is None:
        status = "unknown"
        rate: float | None = None
    else:
        total = entry.get("success", 0) + entry.get("failure", 0)
        rate = entry["success"] / total if total > 0 else None
        status = _status_for(rate)

    label_val = f"{rate * 100:.0f}%" if rate is not None else "no data"

    return {
        "schemaVersion": 1,
        "label": job_id,
        "message": f"{status} ({label_val})",
        "color": _COLOR_MAP[status],
    }


def write_badge(job_id: str, metrics_path: str, output_path: str) -> None:
    """Write the badge JSON for *job_id* to *output_path*."""
    badge = build_badge(job_id, metrics_path)
    Path(output_path).write_text(json.dumps(badge, indent=2))


def badge_summary(metrics_path: str) -> list[dict[str, Any]]:
    """Return badge dicts for every job recorded in *metrics_path*."""
    metrics = load_metrics(metrics_path)
    return [build_badge(job_id, metrics_path) for job_id in sorted(metrics)]
