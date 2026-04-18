import os
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    command: str
    timeout: int = 3600
    retries: int = 0
    retry_delay: int = 5
    log_file: Optional[str] = None
    alert_email: Optional[str] = None
    alert_on_failure: bool = True
    alert_on_success: bool = False
    env: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def from_file(cls, path: str) -> "Config":
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "timeout": self.timeout,
            "retries": self.retries,
            "retry_delay": self.retry_delay,
            "log_file": self.log_file,
            "alert_email": self.alert_email,
            "alert_on_failure": self.alert_on_failure,
            "alert_on_success": self.alert_on_success,
            "env": self.env,
        }

    def validate(self) -> None:
        if not self.command or not self.command.strip():
            raise ValueError("'command' must be a non-empty string")
        if self.timeout <= 0:
            raise ValueError("'timeout' must be a positive integer")
        if self.retries < 0:
            raise ValueError("'retries' must be >= 0")
        if self.retry_delay < 0:
            raise ValueError("'retry_delay' must be >= 0")
