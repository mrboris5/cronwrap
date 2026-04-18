"""Configuration for cronwrap."""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

from cronwrap.alerting import AlertConfig


@dataclass
class Config:
    job_name: str = "unnamed"
    command: str = ""
    retries: int = 0
    retry_delay: float = 5.0
    timeout: Optional[float] = None
    log_level: str = "INFO"
    log_file: Optional[str] = None
    alert: AlertConfig = field(default_factory=AlertConfig)


def from_dict(data: dict) -> Config:
    known = {
        "job_name", "command", "retries", "retry_delay",
        "timeout", "log_level", "log_file", "alert",
    }
    filtered = {k: v for k, v in data.items() if k in known}
    alert_data = filtered.pop("alert", {})
    alert_cfg = AlertConfig(**{k: v for k, v in alert_data.items() if hasattr(AlertConfig, k) or True})
    # Only pass valid AlertConfig fields
    alert_fields = {f.name for f in AlertConfig.__dataclass_fields__.values()}
    alert_cfg = AlertConfig(**{k: v for k, v in alert_data.items() if k in alert_fields})
    return Config(**filtered, alert=alert_cfg)


def from_file(path: str) -> Config:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as fh:
        data = json.load(fh)
    return from_dict(data)


def to_dict(cfg: Config) -> dict:
    d = asdict(cfg)
    return d


def validate(cfg: Config) -> list:
    errors = []
    if not cfg.command:
        errors.append("'command' must not be empty")
    if cfg.retries < 0:
        errors.append("'retries' must be >= 0")
    if cfg.retry_delay < 0:
        errors.append("'retry_delay' must be >= 0")
    if cfg.timeout is not None and cfg.timeout <= 0:
        errors.append("'timeout' must be > 0 if set")
    if cfg.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        errors.append(f"'log_level' invalid: {cfg.log_level}")
    return errors
