import logging
import sys
from pathlib import Path
from typing import Optional


DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    fmt: str = DEFAULT_FORMAT,
) -> logging.Logger:
    """Configure root logger for cronwrap."""
    root = logging.getLogger("cronwrap")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    formatter = logging.Formatter(fmt, datefmt=DEFAULT_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
        root.debug("File logging enabled: %s", path)

    return root


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"cronwrap.{name}")
