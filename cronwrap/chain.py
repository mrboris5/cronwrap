"""Job chaining: define ordered sequences of jobs and track their execution state."""

import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_MAX = 200


def load_chains(path: str) -> Dict[str, dict]:
    """Load chain definitions from a JSON file."""
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_chains(path: str, chains: Dict[str, dict]) -> None:
    """Persist chain definitions to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(chains, indent=2))


def register_chain(path: str, chain_id: str, steps: List[str], description: str = "") -> dict:
    """Register or update a named chain with an ordered list of job steps."""
    if not steps:
        raise ValueError("A chain must have at least one step.")
    chains = load_chains(path)
    entry = {
        "chain_id": chain_id,
        "steps": steps,
        "description": description,
        "current_index": 0,
        "status": "pending",
    }
    chains[chain_id] = entry
    save_chains(path, chains)
    return entry


def get_chain(path: str, chain_id: str) -> Optional[dict]:
    """Return the chain entry for *chain_id*, or None if not found."""
    return load_chains(path).get(chain_id)


def remove_chain(path: str, chain_id: str) -> bool:
    """Remove a chain by id. Returns True if it existed."""
    chains = load_chains(path)
    if chain_id not in chains:
        return False
    del chains[chain_id]
    save_chains(path, chains)
    return True


def advance_chain(path: str, chain_id: str) -> dict:
    """Mark the current step as done and advance to the next one.

    Sets status to 'complete' when all steps are finished.
    Raises KeyError if the chain does not exist.
    """
    chains = load_chains(path)
    if chain_id not in chains:
        raise KeyError(f"Chain not found: {chain_id}")
    entry = chains[chain_id]
    idx = entry["current_index"] + 1
    if idx >= len(entry["steps"]):
        entry["current_index"] = len(entry["steps"])
        entry["status"] = "complete"
    else:
        entry["current_index"] = idx
        entry["status"] = "running"
    chains[chain_id] = entry
    save_chains(path, chains)
    return entry


def current_step(chain: dict) -> Optional[str]:
    """Return the current step name, or None if the chain is complete."""
    idx = chain.get("current_index", 0)
    steps = chain.get("steps", [])
    if idx >= len(steps):
        return None
    return steps[idx]
