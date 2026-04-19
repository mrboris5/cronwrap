"""Tag and label support for cron jobs."""
from typing import Dict, List, Optional


def parse_tags(raw: str) -> Dict[str, str]:
    """Parse 'key=value,key2=value2' or 'tag1,tag2' into a dict."""
    tags: Dict[str, str] = {}
    if not raw or not raw.strip():
        return tags
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            k, _, v = part.partition("=")
            tags[k.strip()] = v.strip()
        else:
            tags[part] = "true"
    return tags


def format_tags(tags: Dict[str, str]) -> str:
    """Serialize tags dict back to string."""
    return ",".join(
        f"{k}={v}" if v != "true" else k for k, v in sorted(tags.items())
    )


def filter_by_tag(jobs: List[Dict], key: str, value: Optional[str] = None) -> List[Dict]:
    """Return jobs whose tags contain key (and optionally match value)."""
    result = []
    for job in jobs:
        tags = job.get("tags", {})
        if key in tags:
            if value is None or tags[key] == value:
                result.append(job)
    return result


def merge_tags(base: Dict[str, str], override: Dict[str, str]) -> Dict[str, str]:
    """Merge two tag dicts; override wins on conflict."""
    merged = dict(base)
    merged.update(override)
    return merged
