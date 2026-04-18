"""Configuration model for cronwrap."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    command: str = ""
    retries: int = 0
    retry_delay: float = 5.0
    timeout: Optional[float] = None
    log_file: Optional[str] = None
    log_level: str = "INFO"
    alert_email: Optional[str] = None
    alert_on_failure: bool = True
    alert_on_success: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 25
    lock_dir: Optional[str] = None
    lock_timeout: int = 0
    job_name: Optional[str] = None


KNOWN_KEYS = set(Config.__dataclass_fields__.keys())


def from_dict(data: dict) -> Config:
    filtered = {k: v for k, v in data.items() if k in KNOWN_KEYS}
    return Config(**filtered)


def from_file(path: str) -> Config:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with p.open() as f:
        data = json.load(f)
    return from_dict(data)


def to_dict(cfg: Config) -> dict:
    return asdict(cfg)


def validate(cfg: Config) -> list:
    errors = []
    if not cfg.command:
        errors.append("'command' is required and cannot be empty")
    if cfg.retries < 0:
        errors.append("'retries' must be >= 0")
    if cfg.retry_delay < 0:
        errors.append("'retry_delay' must be >= 0")
    if cfg.timeout is not None and cfg.timeout <= 0:
        errors.append("'timeout' must be > 0 if specified")
    if cfg.smtp_port < 1 or cfg.smtp_port > 65535:
        errors.append("'smtp_port' must be between 1 and 65535")
    if cfg.lock_timeout < 0:
        errors.append("'lock_timeout' must be >= 0")
    return errors
