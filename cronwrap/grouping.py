"""Group and summarize jobs by tag."""
from typing import Dict, List, Any
from cronwrap.tags import filter_by_tag


def group_by_tag(jobs: List[Dict], key: str) -> Dict[str, List[Dict]]:
    """Group jobs into buckets by the value of a tag key."""
    groups: Dict[str, List[Dict]] = {}
    for job in jobs:
        value = job.get("tags", {}).get(key, "__untagged__")
        groups.setdefault(value, []).append(job)
    return groups


def tag_summary(jobs: List[Dict]) -> Dict[str, int]:
    """Return count of jobs per unique tag key."""
    counts: Dict[str, int] = {}
    for job in jobs:
        for k in job.get("tags", {}):
            counts[k] = counts.get(k, 0) + 1
    return counts


def jobs_with_all_tags(jobs: List[Dict], required: Dict[str, str]) -> List[Dict]:
    """Return jobs that match ALL key=value pairs in required."""
    result = jobs
    for k, v in required.items():
        result = filter_by_tag(result, k, v)
    return result
