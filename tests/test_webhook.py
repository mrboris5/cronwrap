"""Tests for cronwrap.webhook and cronwrap.dispatch."""
import json
from unittest.mock import patch, MagicMock
import urllib.error

import pytest

from cronwrap.webhook import WebhookConfig, build_payload, send_webhook
from cronwrap.dispatch import dispatch
from cronwrap.notify import SMTPConfig


def test_build_payload_basic():
    p = build_payload("subj", "body")
    assert p == {"subject": "subj", "body": "body"}


def test_build_payload_extra():
    p = build_payload("s", "b", {"exit_code": 1})
    assert p["exit_code"] == 1


def test_send_webhook_no_url():
    cfg = WebhookConfig(url="")
    assert send_webhook(cfg, "s", "b") is False


def test_send_webhook_success():
    cfg = WebhookConfig(url="http://example.com/hook")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = send_webhook(cfg, "subj", "body")
    assert result is True


def test_send_webhook_http_error():
    cfg = WebhookConfig(url="http://example.com/hook")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("err")):
        result = send_webhook(cfg, "s", "b")
    assert result is False


def test_dispatch_both_backends():
    smtp_cfg = SMTPConfig(to_addrs=["a@b.com"])
    wh_cfg = WebhookConfig(url="http://hook.example.com")
    with patch("cronwrap.dispatch.send_email", return_value=True) as me, \
         patch("cronwrap.dispatch.send_webhook", return_value=True) as mw:
        results = dispatch("s", "b", smtp_cfg=smtp_cfg, webhook_cfg=wh_cfg)
    assert results == {"email": True, "webhook": True}


def test_dispatch_no_backends():
    results = dispatch("s", "b")
    assert results == {}
