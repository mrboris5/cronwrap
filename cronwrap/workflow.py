"""Workflow: define and track multi-step job pipelines."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_MAX = 200


def load_workflows(path: str) -> Dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_workflows(path: str, data: Dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def register_workflow(path: str, workflow_id: str, steps: List[str],
                      description: str = "") -> Dict:
    """Register or overwrite a workflow definition."""
    data = load_workflows(path)
    data[workflow_id] = {
        "workflow_id": workflow_id,
        "steps": steps,
        "description": description,
    }
    save_workflows(path, data)
    return data[workflow_id]


def get_workflow(path: str, workflow_id: str) -> Optional[Dict]:
    return load_workflows(path).get(workflow_id)


def remove_workflow(path: str, workflow_id: str) -> bool:
    data = load_workflows(path)
    if workflow_id not in data:
        return False
    del data[workflow_id]
    save_workflows(path, data)
    return True


def list_workflows(path: str) -> List[Dict]:
    return list(load_workflows(path).values())


def workflow_step_index(path: str, workflow_id: str, step: str) -> int:
    """Return 0-based index of *step* in *workflow_id*, or -1 if not found."""
    wf = get_workflow(path, workflow_id)
    if wf is None:
        return -1
    try:
        return wf["steps"].index(step)
    except ValueError:
        return -1
