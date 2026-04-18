"""Alerting module for cronwrap — sends notifications on job failure."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_addr: str = "cronwrap@localhost"
    to_addrs: list = field(default_factory=list)
    use_tls: bool = False


def build_message(job_name: str, command: str, returncode: int, output: str, from_addr: str, to_addrs: list) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = f"[cronwrap] Job '{job_name}' failed (exit {returncode})"
    body = (
        f"Job: {job_name}\n"
        f"Command: {command}\n"
        f"Exit code: {returncode}\n\n"
        f"Output:\n{output}"
    )
    msg.attach(MIMEText(body, "plain"))
    return msg


def send_alert(alert_cfg: AlertConfig, job_name: str, command: str, returncode: int, output: str) -> bool:
    """Send an alert email. Returns True on success, False on failure."""
    if not alert_cfg.enabled or not alert_cfg.to_addrs:
        logger.debug("Alerting disabled or no recipients configured, skipping.")
        return False

    msg = build_message(job_name, command, returncode, output, alert_cfg.from_addr, alert_cfg.to_addrs)

    try:
        if alert_cfg.use_tls:
            server = smtplib.SMTP_SSL(alert_cfg.smtp_host, alert_cfg.smtp_port)
        else:
            server = smtplib.SMTP(alert_cfg.smtp_host, alert_cfg.smtp_port)

        if alert_cfg.smtp_user and alert_cfg.smtp_password:
            server.login(alert_cfg.smtp_user, alert_cfg.smtp_password)

        server.sendmail(alert_cfg.from_addr, alert_cfg.to_addrs, msg.as_string())
        server.quit()
        logger.info("Alert sent for job '%s' to %s", job_name, alert_cfg.to_addrs)
        return True
    except Exception as exc:
        logger.error("Failed to send alert: %s", exc)
        return False
