"""Job-scoped variable storage: persist named key/value pairs per job."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

_DEFAULT_MAX = 500


def load_variables(path: str) -> Dict[str, Dict[str, Any]]:
    """Load variables from *path*; return empty dict on missing/corrupt file."""
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_variables(path: str, data: Dict[str, Dict[str, Any]]) -> None:
    """Persist *data* to *path*, creating parent directories as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def set_variable(path: str, job_id: str, key: str, value: Any) -> Dict[str, Any]:
    """Set *key* = *value* for *job_id* and return the updated variable map."""
    data = load_variables(path)
    if job_id not in data:
        data[job_id] = {}
    data[job_id][key] = value
    save_variables(path, data)
    return dict(data[job_id])


def get_variable(path: str, job_id: str, key: str) -> Optional[Any]:
    """Return the value stored under *key* for *job_id*, or None."""
    data = load_variables(path)
    return data.get(job_id, {}).get(key)


def get_all_variables(path: str, job_id: str) -> Dict[str, Any]:
    """Return all variables stored for *job_id*."""
    data = load_variables(path)
    return dict(data.get(job_id, {}))


def remove_variable(path: str, job_id: str, key: str) -> bool:
    """Remove *key* from *job_id*'s variables. Return True if it existed."""
    data = load_variables(path)
    job_vars = data.get(job_id, {})
    if key not in job_vars:
        return False
    del job_vars[key]
    if job_vars:
        data[job_id] = job_vars
    else:
        data.pop(job_id, None)
    save_variables(path, data)
    return True


def clear_variables(path: str, job_id: str) -> int:
    """Remove all variables for *job_id*. Return the number removed."""
    data = load_variables(path)
    count = len(data.get(job_id, {}))
    data.pop(job_id, None)
    save_variables(path, data)
    return count
