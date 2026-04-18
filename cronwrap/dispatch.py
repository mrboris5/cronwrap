"""Dispatch notifications via configured backends."""
from __future__ import annotations

from typing import Optional, Dict, Any

from cronwrap.notify import SMTPConfig, send_email
from cronwrap.webhook import WebhookConfig, send_webhook


def dispatch(
    subject: str,
    body: str,
    smtp_cfg: Optional[SMTPConfig] = None,
    webhook_cfg: Optional[WebhookConfig] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """Send notification via all enabled backends.

    Returns a dict mapping backend name to success status.
    """
    results: Dict[str, bool] = {}

    if smtp_cfg is not None and smtp_cfg.to_addrs:
        results["email"] = send_email(smtp_cfg, subject, body)

    if webhook_cfg is not None and webhook_cfg.url:
        results["webhook"] = send_webhook(webhook_cfg, subject, body, extra)

    return results
