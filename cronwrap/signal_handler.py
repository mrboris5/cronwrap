"""Signal handling for graceful shutdown of cron jobs."""

import os
import signal
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

_shutdown_requested = False
_cleanup_callbacks: list[Callable[[], None]] = []


def is_shutdown_requested() -> bool:
    """Return True if a shutdown signal has been received."""
    return _shutdown_requested


def register_cleanup(fn: Callable[[], None]) -> None:
    """Register a callback to be called on shutdown signal."""
    _cleanup_callbacks.append(fn)


def clear_cleanups() -> None:
    """Remove all registered cleanup callbacks (useful in tests)."""
    global _shutdown_requested
    _cleanup_callbacks.clear()
    _shutdown_requested = False


def _handle_signal(signum: int, frame) -> None:  # noqa: ANN001
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.warning("Received signal %s — requesting graceful shutdown", sig_name)
    _shutdown_requested = True
    for cb in _cleanup_callbacks:
        try:
            cb()
        except Exception as exc:  # noqa: BLE001
            logger.error("Cleanup callback raised: %s", exc)


def install_signal_handlers(signals: Optional[list[int]] = None) -> None:
    """Install handlers for SIGTERM and SIGINT (or a custom list)."""
    if signals is None:
        signals = [signal.SIGTERM, signal.SIGINT]
    for sig in signals:
        signal.signal(sig, _handle_signal)
        logger.debug("Installed handler for %s", signal.Signals(sig).name)


def reset() -> None:
    """Reset module state; restores default signal handlers."""
    global _shutdown_requested
    _shutdown_requested = False
    _cleanup_callbacks.clear()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, signal.SIG_DFL)
