"""Timeout utilities for cronwrap."""

from __future__ import annotations

import signal
import threading
from contextlib import contextmanager
from typing import Optional


class TimeoutExpired(Exception):
    """Raised when a job exceeds its allowed runtime."""

    def __init__(self, seconds: int):
        self.seconds = seconds
        super().__init__(f"Job timed out after {seconds}s")


@contextmanager
def timeout(seconds: int):
    """
    Context manager that raises TimeoutExpired if the block takes longer
    than *seconds* seconds.  Uses SIGALRM on Unix; falls back to a
    threading.Timer on platforms without SIGALRM.
    """
    if seconds <= 0:
        yield
        return

    if hasattr(signal, "SIGALRM"):
        def _handler(signum, frame):  # noqa: ANN001
            raise TimeoutExpired(seconds)

        old = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    else:
        # Windows fallback — best-effort via thread
        expired: list[bool] = [False]
        current = threading.current_thread()

        def _raise():
            expired[0] = True
            # Cannot reliably interrupt another thread; just set flag

        timer = threading.Timer(seconds, _raise)
        timer.daemon = True
        timer.start()
        try:
            yield
            if expired[0]:
                raise TimeoutExpired(seconds)
        finally:
            timer.cancel()


def parse_timeout(value: Optional[str]) -> Optional[int]:
    """Parse a timeout string ('30s', '5m', '1h') to seconds, or None."""
    if value is None:
        return None
    value = value.strip()
    units = {"s": 1, "m": 60, "h": 3600}
    if value[-1] in units:
        return int(value[:-1]) * units[value[-1]]
    return int(value)  # bare integer treated as seconds
