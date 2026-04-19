"""In-memory job registry with tag-based lookup."""
from typing import Dict, List, Optional
from cronwrap.tags import parse_tags, merge_tags
from cronwrap.grouping import jobs_with_all_tags


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: Dict[str, Dict] = {}

    def register(self, job_id: str, command: str, tags: str = "", **meta) -> None:
        """Register a job with optional tags and metadata."""
        if job_id in self._jobs:
            raise ValueError(f"Job '{job_id}' already registered")
        self._jobs[job_id] = {
            "id": job_id,
            "command": command,
            "tags": parse_tags(tags),
            **meta,
        }

    def get(self, job_id: str) -> Optional[Dict]:
        return self._jobs.get(job_id)

    def all(self) -> List[Dict]:
        return list(self._jobs.values())

    def find(self, **tag_filters: str) -> List[Dict]:
        """Find jobs matching all provided tag key=value pairs."""
        return jobs_with_all_tags(self.all(), tag_filters)

    def unregister(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def update_tags(self, job_id: str, tags: str) -> None:
        if job_id not in self._jobs:
            raise KeyError(f"Job '{job_id}' not found")
        self._jobs[job_id]["tags"] = merge_tags(
            self._jobs[job_id]["tags"], parse_tags(tags)
        )

    def __len__(self) -> int:
        return len(self._jobs)
