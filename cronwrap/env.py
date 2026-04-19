"""Environment variable injection and validation for cron jobs."""
from __future__ import annotations

import os
from typing import Dict, List, Optional


class EnvError(Exception):
    """Raised when required environment variables are missing."""


def require_vars(names: List[str]) -> None:
    """Raise EnvError if any of the named env vars are not set."""
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise EnvError(f"Missing required environment variables: {', '.join(missing)}")


def load_env_file(path: str) -> Dict[str, str]:
    """Parse a simple KEY=VALUE env file, ignoring comments and blank lines."""
    pairs: Dict[str, str] = {}
    with open(path) as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise EnvError(f"Invalid env file line {lineno}: {line!r}")
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not key:
                raise EnvError(f"Empty key on line {lineno}")
            pairs[key] = value
    return pairs


def inject_env(pairs: Dict[str, str], override: bool = False) -> None:
    """Set environment variables from a dict."""
    for key, value in pairs.items():
        if override or key not in os.environ:
            os.environ[key] = value


def apply_env_file(path: str, override: bool = False) -> Dict[str, str]:
    """Load an env file and inject its variables into the process environment."""
    pairs = load_env_file(path)
    inject_env(pairs, override=override)
    return pairs


def get_with_default(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return env var value or default."""
    return os.environ.get(name, default)
