"""Tests for cronwrap.signal_handler."""

import signal
import pytest

import cronwrap.signal_handler as sh


@pytest.fixture(autouse=True)
def _reset():
    """Ensure clean state before and after every test."""
    sh.reset()
    yield
    sh.reset()


def test_initial_state_not_shutdown():
    assert sh.is_shutdown_requested() is False


def test_handle_signal_sets_flag():
    sh._handle_signal(signal.SIGTERM, None)
    assert sh.is_shutdown_requested() is True


def test_handle_signal_runs_callbacks():
    called = []
    sh.register_cleanup(lambda: called.append(1))
    sh._handle_signal(signal.SIGTERM, None)
    assert called == [1]


def test_multiple_callbacks_all_called():
    log = []
    sh.register_cleanup(lambda: log.append("a"))
    sh.register_cleanup(lambda: log.append("b"))
    sh._handle_signal(signal.SIGINT, None)
    assert log == ["a", "b"]


def test_callback_exception_does_not_abort_others():
    log = []

    def bad():
        raise RuntimeError("boom")

    sh.register_cleanup(bad)
    sh.register_cleanup(lambda: log.append("ok"))
    sh._handle_signal(signal.SIGTERM, None)  # should not raise
    assert log == ["ok"]


def test_clear_cleanups_removes_callbacks():
    sh.register_cleanup(lambda: None)
    sh.clear_cleanups()
    # trigger signal — no callbacks should run (no error)
    sh._handle_signal(signal.SIGTERM, None)
    assert sh.is_shutdown_requested() is False  # clear_cleanups also resets flag


def test_install_signal_handlers_sets_custom_handler():
    sh.install_signal_handlers([signal.SIGUSR1])
    handler = signal.getsignal(signal.SIGUSR1)
    assert handler == sh._handle_signal
    # restore
    signal.signal(signal.SIGUSR1, signal.SIG_DFL)


def test_reset_restores_default_handlers():
    sh.install_signal_handlers()
    sh.reset()
    assert signal.getsignal(signal.SIGTERM) == signal.SIG_DFL
    assert signal.getsignal(signal.SIGINT) == signal.SIG_DFL


def test_reset_clears_shutdown_flag():
    sh._handle_signal(signal.SIGTERM, None)
    assert sh.is_shutdown_requested() is True
    sh.reset()
    assert sh.is_shutdown_requested() is False
