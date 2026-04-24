"""Job output similarity comparison — detect anomalous output by comparing
against a stored baseline output fingerprint."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Optional

_DEFAULT_PATH = os.path.expanduser("~/.cronwrap/similarity.json")


def _load(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data: dict, path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def _fingerprint(text: str) -> str:
    """Return a stable fingerprint: sorted unique non-empty lines, hashed."""
    lines = sorted(set(l.strip() for l in text.splitlines() if l.strip()))
    digest = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    return digest


def _token_set(text: str) -> set[str]:
    """Return a set of word tokens from *text* for Jaccard similarity."""
    return set(re.findall(r"\w+", text.lower()))


def jaccard(a: str, b: str) -> float:
    """Jaccard similarity between token sets of *a* and *b* (0.0–1.0)."""
    sa, sb = _token_set(a), _token_set(b)
    if not sa and not sb:
        return 1.0
    union = sa | sb
    return len(sa & sb) / len(union)


def store_baseline(job_id: str, output: str, path: str = _DEFAULT_PATH) -> str:
    """Store the baseline output for *job_id*; return its fingerprint."""
    data = _load(path)
    fp = _fingerprint(output)
    data[job_id] = {"fingerprint": fp, "sample": output[:2000]}
    _save(data, path)
    return fp


def get_baseline(job_id: str, path: str = _DEFAULT_PATH) -> Optional[dict]:
    """Return the stored baseline dict for *job_id*, or None."""
    return _load(path).get(job_id)


def compare_output(
    job_id: str,
    output: str,
    threshold: float = 0.5,
    path: str = _DEFAULT_PATH,
) -> dict:
    """Compare *output* against the stored baseline.

    Returns a dict with keys: similar (bool), score (float), baseline_found (bool).
    """
    baseline = get_baseline(job_id, path)
    if baseline is None:
        return {"similar": True, "score": 1.0, "baseline_found": False}
    score = jaccard(baseline["sample"], output)
    return {"similar": score >= threshold, "score": round(score, 4), "baseline_found": True}


def similarity_reason(job_id: str, output: str, threshold: float = 0.5, path: str = _DEFAULT_PATH) -> str:
    result = compare_output(job_id, output, threshold, path)
    if not result["baseline_found"]:
        return f"no baseline stored for job '{job_id}'"
    if result["similar"]:
        return f"output is similar to baseline (score={result['score']})"
    return f"output differs from baseline (score={result['score']}, threshold={threshold})"
