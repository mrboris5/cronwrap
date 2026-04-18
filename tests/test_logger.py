import logging
import pytest
from pathlib import Path
from cronwrap.logger import setup_logging, get_logger


def test_setup_logging_returns_logger():
    log = setup_logging()
    assert isinstance(log, logging.Logger)
    assert log.name == "cronwrap"


def test_setup_logging_level():
    log = setup_logging(level="DEBUG")
    assert log.level == logging.DEBUG


def test_setup_logging_invalid_level_defaults_to_info():
    log = setup_logging(level="NOTALEVEL")
    assert log.level == logging.INFO


def test_setup_logging_has_console_handler():
    log = setup_logging()
    assert any(isinstance(h, logging.StreamHandler) for h in log.handlers)


def test_setup_logging_file_handler(tmp_path):
    log_file = str(tmp_path / "logs" / "cronwrap.log")
    log = setup_logging(log_file=log_file)
    assert Path(log_file).parent.exists()
    handlers = [type(h).__name__ for h in log.handlers]
    assert "FileHandler" in handlers


def test_get_logger_namespace():
    log = get_logger("runner")
    assert log.name == "cronwrap.runner"


def test_setup_logging_clears_previous_handlers():
    setup_logging()
    setup_logging()
    log = logging.getLogger("cronwrap")
    assert len(log.handlers) == 1
