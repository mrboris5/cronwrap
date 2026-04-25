"""Formatted SLA reports for cronwrap jobs."""

from cronwrap.sla import load_sla_records, sla_compliance


def _bar(rate: float, width: int = 20) -> str:
    """Render a simple ASCII progress bar for a compliance rate."""
    filled = round(rate * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def format_sla_entry(job_id: str, entry: dict) -> str:
    """Format a single job's SLA entry as a report string."""
    total = entry.get("total", 0)
    violations = entry.get("violations", 0)
    compliance = (1.0 - violations / total) if total else 1.0
    bar = _bar(compliance)
    last = entry.get("last_run") or "never"
    lines = [
        f"Job:        {job_id}",
        f"Runs:       {total}",
        f"Violations: {violations}",
        f"Compliance: {bar} {compliance * 100:.1f}%",
        f"Last run:   {last}",
    ]
    return "\n".join(lines)


def format_sla_summary(path: str) -> str:
    """Format a multi-job SLA summary table."""
    records = load_sla_records(path)
    if not records:
        return "No SLA records found."

    header = f"{'Job':<30} {'Runs':>6} {'Violations':>10} {'Compliance':>12}"
    divider = "-" * len(header)
    rows = [header, divider]
    for job_id in sorted(records):
        entry = records[job_id]
        total = entry.get("total", 0)
        violations = entry.get("violations", 0)
        compliance = sla_compliance(path, job_id) * 100
        rows.append(f"{job_id:<30} {total:>6} {violations:>10} {compliance:>11.1f}%")
    return "\n".join(rows)


def print_sla_report(path: str) -> None:
    """Print the full SLA summary to stdout."""
    print(format_sla_summary(path))
