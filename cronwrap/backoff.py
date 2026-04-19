"""Exponential backoff calculation for retry delays."""
from __future__ import annotations
import random
from typing import Iterator


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def backoff_delays(
    base: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 300.0,
    jitter: bool = True,
    max_retries: int = 5,
) -> Iterator[float]:
    """Yield successive delay values (seconds) for retry attempts.

    Args:
        base: Initial delay in seconds.
        factor: Multiplicative growth factor per attempt.
        max_delay: Upper bound on delay.
        jitter: If True, add uniform random jitter up to current delay.
        max_retries: Number of delays to yield.
    """
    if base <= 0:
        raise ValueError("base must be positive")
    if factor < 1:
        raise ValueError("factor must be >= 1")
    if max_delay < base:
        raise ValueError("max_delay must be >= base")

    delay = base
    for _ in range(max_retries):
        actual = _clamp(delay, base, max_delay)
        if jitter:
            actual = random.uniform(0, actual)
        yield actual
        delay = min(delay * factor, max_delay)


def next_delay(
    attempt: int,
    base: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 300.0,
    jitter: bool = False,
) -> float:
    """Return delay for a specific attempt index (0-based)."""
    if attempt < 0:
        raise ValueError("attempt must be >= 0")
    delay = min(base * (factor ** attempt), max_delay)
    if jitter:
        delay = random.uniform(0, delay)
    return delay
