"""Tests for cronwrap.alerting module."""

import pytest
from unittest.mock import patch, MagicMock
from cronwrap.alerting import AlertConfig, build_message, send_alert


def make_cfg(**kwargs):
    defaults = dict(enabled=True, to_addrs=["ops@example.com"], smtp_host="localhost", smtp_port=25)
    defaults.update(kwargs)
    return AlertConfig(**defaults)


def test_alert_config_defaults():
    cfg = AlertConfig()
    assert cfg.enabled is False
    assert cfg.smtp_port == 25
    assert cfg.to_addrs == []
    assert cfg.use_tls is False


def test_build_message_subject():
    msg = build_message("backup", "tar -czf ...", 1, "error output", "from@x.com", ["to@x.com"])
    assert "backup" in msg["Subject"]
    assert "exit 1" in msg["Subject"]


def test_build_message_body_contains_command():
    msg = build_message("myjob", "echo hello", 2, "some output", "f@f.com", ["t@t.com"])
    payload = msg.get_payload(0).get_payload()
    assert "echo hello" in payload
    assert "some output" in payload


def test_send_alert_disabled_returns_false():
    cfg = AlertConfig(enabled=False, to_addrs=["a@b.com"])
    result = send_alert(cfg, "job", "cmd", 1, "out")
    assert result is False


def test_send_alert_no_recipients_returns_false():
    cfg = AlertConfig(enabled=True, to_addrs=[])
    result = send_alert(cfg, "job", "cmd", 1, "out")
    assert result is False


def test_send_alert_success():
    cfg = make_cfg()
    with patch("cronwrap.alerting.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        result = send_alert(cfg, "myjob", "ls -la", 1, "output")
    assert result is True
    mock_server.sendmail.assert_called_once()
    mock_server.quit.assert_called_once()


def test_send_alert_uses_tls():
    cfg = make_cfg(use_tls=True)
    with patch("cronwrap.alerting.smtplib.SMTP_SSL") as mock_ssl:
        mock_server = MagicMock()
        mock_ssl.return_value = mock_server
        result = send_alert(cfg, "job", "cmd", 1, "out")
    assert result is True
    mock_ssl.assert_called_once_with("localhost", 25)


def test_send_alert_smtp_error_returns_false():
    cfg = make_cfg()
    with patch("cronwrap.alerting.smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
        result = send_alert(cfg, "job", "cmd", 1, "out")
    assert result is False


def test_send_alert_with_credentials():
    cfg = make_cfg(smtp_user="user", smtp_password="pass")
    with patch("cronwrap.alerting.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server
        send_alert(cfg, "job", "cmd", 1, "out")
    mock_server.login.assert_called_once_with("user", "pass")
