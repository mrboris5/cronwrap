"""Feature flag support for cronwrap jobs."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

_DEFAULT_PATH = ".cronwrap_flags.json"


def load_flags(path: str = _DEFAULT_PATH) -> Dict[str, Any]:
    """Load feature flags from a JSON file."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_flags(flags: Dict[str, Any], path: str = _DEFAULT_PATH) -> None:
    """Persist feature flags to a JSON file."""
    Path(path).write_text(json.dumps(flags, indent=2))


def set_flag(name: str, value: Any, path: str = _DEFAULT_PATH) -> Dict[str, Any]:
    """Set a feature flag by name."""
    flags = load_flags(path)
    flags[name] = value
    save_flags(flags, path)
    return flags


def get_flag(name: str, default: Any = None, path: str = _DEFAULT_PATH) -> Any:
    """Retrieve a feature flag value, returning default if not set."""
    flags = load_flags(path)
    return flags.get(name, default)


def remove_flag(name: str, path: str = _DEFAULT_PATH) -> bool:
    """Remove a feature flag. Returns True if it existed."""
    flags = load_flags(path)
    if name not in flags:
        return False
    del flags[name]
    save_flags(flags, path)
    return True


def is_enabled(name: str, path: str = _DEFAULT_PATH) -> bool:
    """Return True if the flag exists and is truthy."""
    return bool(get_flag(name, default=False, path=path))


def all_flags(path: str = _DEFAULT_PATH) -> Dict[str, Any]:
    """Return all defined feature flags."""
    return load_flags(path)


def flag_summary(path: str = _DEFAULT_PATH) -> str:
    """Return a human-readable summary of all flags."""
    flags = load_flags(path)
    if not flags:
        return "No feature flags defined."
    lines = ["Feature Flags:"]
    for name, value in sorted(flags.items()):
        lines.append(f"  {name}: {value}")
    return "\n".join(lines)
