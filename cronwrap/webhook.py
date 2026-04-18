"""Webhook notification backend for cronwrap."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class WebhookConfig:
    url: str = ""
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json"})
    timeout: int = 10


def build_payload(subject: str, body: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"subject": subject, "body": body}
    if extra:
        payload.update(extra)
    return payload


def send_webhook(cfg: WebhookConfig, subject: str, body: str,
                 extra: Optional[Dict[str, Any]] = None) -> bool:
    """POST a JSON payload to the configured webhook URL. Returns True on success."""
    if not cfg.url:
        return False
    payload = build_payload(subject, body, extra)
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        cfg.url,
        data=data,
        headers=cfg.headers,
        method=cfg.method,
    )
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, OSError):
        return False
