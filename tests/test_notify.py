"""Tests for cronwrap.notify (SMTP backend)."""
import os
import smtplib
from unittest.mock import patch, MagicMock

import pytest

from cronwrap.notify import SMTPConfig, send_email


def test_smtp_config_defaults():
    cfg = SMTPConfig()
    assert cfg.host == "localhost"
    assert cfg.port == 25
    assert cfg.use_tls is False
    assert cfg.to_addrs == []


def test_smtp_config_from_env(monkeypatch):
    monkeypatch.setenv("CRONWRAP_SMTP_HOST", "mail.example.com")
    monkeypatch.setenv("CRONWRAP_SMTP_PORT", "587")
    monkeypatch.setenv("CRONWRAP_SMTP_TLS", "true")
    monkeypatch.setenv("CRONWRAP_SMTP_TO", "a@b.com, c@d.com")
    cfg = SMTPConfig.from_env()
    assert cfg.host == "mail.example.com"
    assert cfg.port == 587
    assert cfg.use_tls is True
    assert cfg.to_addrs == ["a@b.com", "c@d.com"]


def test_send_email_no_recipients():
    cfg = SMTPConfig(to_addrs=[])
    assert send_email(cfg, "subj", "body") is False


def test_send_email_success():
    cfg = SMTPConfig(to_addrs=["x@y.com"])
    mock_server = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_server):
        result = send_email(cfg, "Hello", "World")
    assert result is True
    mock_server.sendmail.assert_called_once()
    mock_server.quit.assert_called_once()


def test_send_email_smtp_error():
    cfg = SMTPConfig(to_addrs=["x@y.com"])
    with patch("smtplib.SMTP", side_effect=smtplib.SMTPException("fail")):
        result = send_email(cfg, "subj", "body")
    assert result is False


def test_send_email_tls():
    cfg = SMTPConfig(to_addrs=["x@y.com"], use_tls=True)
    mock_server = MagicMock()
    with patch("smtplib.SMTP_SSL", return_value=mock_server):
        result = send_email(cfg, "subj", "body")
    assert result is True
