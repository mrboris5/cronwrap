"""Notification backends for cronwrap alerts."""
from __future__ import annotations

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SMTPConfig:
    host: str = "localhost"
    port: int = 25
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = False
    from_addr: str = "cronwrap@localhost"
    to_addrs: list = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "SMTPConfig":
        return cls(
            host=os.environ.get("CRONWRAP_SMTP_HOST", "localhost"),
            port=int(os.environ.get("CRONWRAP_SMTP_PORT", "25")),
            username=os.environ.get("CRONWRAP_SMTP_USER"),
            password=os.environ.get("CRONWRAP_SMTP_PASS"),
            use_tls=os.environ.get("CRONWRAP_SMTP_TLS", "").lower() in ("1", "true"),
            from_addr=os.environ.get("CRONWRAP_SMTP_FROM", "cronwrap@localhost"),
            to_addrs=[
                a.strip()
                for a in os.environ.get("CRONWRAP_SMTP_TO", "").split(",")
                if a.strip()
            ],
        )


def send_email(cfg: SMTPConfig, subject: str, body: str) -> bool:
    """Send an email notification. Returns True on success."""
    if not cfg.to_addrs:
        return False
    msg = MIMEMultipart()
    msg["From"] = cfg.from_addr
    msg["To"] = ", ".join(cfg.to_addrs)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        if cfg.use_tls:
            server = smtplib.SMTP_SSL(cfg.host, cfg.port)
        else:
            server = smtplib.SMTP(cfg.host, cfg.port)
        if cfg.username and cfg.password:
            server.login(cfg.username, cfg.password)
        server.sendmail(cfg.from_addr, cfg.to_addrs, msg.as_string())
        server.quit()
        return True
    except smtplib.SMTPException:
        return False
