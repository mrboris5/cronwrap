"""Tag index: fast lookup of jobs by tag."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set

_DEFAULT_PATH = Path(".cronwrap") / "tag_index.json"


def load_index(path: Path = _DEFAULT_PATH) -> Dict[str, List[str]]:
    """Load tag -> [job_id, ...] mapping from disk."""
    try:
        raw = path.read_text()
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        return {k: list(v) for k, v in data.items() if isinstance(v, list)}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_index(index: Dict[str, List[str]], path: Path = _DEFAULT_PATH) -> None:
    """Persist tag index to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, sort_keys=True))


def index_job(job_id: str, tags: List[str], path: Path = _DEFAULT_PATH) -> None:
    """Associate *job_id* with each tag in *tags*, replacing any prior mapping."""
    index = load_index(path)
    # Remove job from all existing tag lists first.
    for tag_jobs in index.values():
        if job_id in tag_jobs:
            tag_jobs.remove(job_id)
    # Add to new tags.
    for tag in tags:
        index.setdefault(tag, [])
        if job_id not in index[tag]:
            index[tag].append(job_id)
    # Drop empty tag entries.
    index = {t: jobs for t, jobs in index.items() if jobs}
    save_index(index, path)


def deindex_job(job_id: str, path: Path = _DEFAULT_PATH) -> None:
    """Remove *job_id* from every tag in the index."""
    index = load_index(path)
    for tag_jobs in index.values():
        if job_id in tag_jobs:
            tag_jobs.remove(job_id)
    index = {t: jobs for t, jobs in index.items() if jobs}
    save_index(index, path)


def jobs_for_tag(tag: str, path: Path = _DEFAULT_PATH) -> List[str]:
    """Return sorted list of job IDs associated with *tag*."""
    index = load_index(path)
    return sorted(index.get(tag, []))


def tags_for_job(job_id: str, path: Path = _DEFAULT_PATH) -> List[str]:
    """Return sorted list of tags associated with *job_id*."""
    index = load_index(path)
    return sorted(tag for tag, jobs in index.items() if job_id in jobs)


def all_tags(path: Path = _DEFAULT_PATH) -> List[str]:
    """Return sorted list of all known tags."""
    return sorted(load_index(path).keys())
