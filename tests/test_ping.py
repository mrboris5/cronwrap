"""Tests for cronwrap.ping module."""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch, MagicMock
from cronwrap.ping import (
    load_pings,
    save_pings,
    set_ping_url,
    get_ping_url,
    remove_ping_url,
    send_ping,
    ping_job,
)


@pytest.fixture
def pfile(tmp_path):
    return str(tmp_path / "pings.json")


def test_load_pings_missing_file(pfile):
    assert load_pings(pfile) == {}


def test_load_pings_corrupt_file(pfile):
    with open(pfile, "w") as f:
        f.write("not json")
    assert load_pings(pfile) == {}


def test_save_and_load_roundtrip(pfile):
    data = {"job1": [{"url": "http://example.com/ping", "method": "GET"}]}
    save_pings(pfile, data)
    loaded = load_pings(pfile)
    assert loaded == data


def test_set_ping_url_creates_entry(pfile):
    entry = set_ping_url(pfile, "myjob", "http://ping.example.com/abc")
    assert entry["url"] == "http://ping.example.com/abc"
    assert entry["method"] == "GET"


def test_set_ping_url_custom_method(pfile):
    entry = set_ping_url(pfile, "myjob", "http://ping.example.com/abc", method="post")
    assert entry["method"] == "POST"


def test_get_ping_url_returns_entry(pfile):
    set_ping_url(pfile, "job1", "http://example.com/1")
    result = get_ping_url(pfile, "job1")
    assert result is not None
    assert result["url"] == "http://example.com/1"


def test_get_ping_url_missing_job(pfile):
    assert get_ping_url(pfile, "nonexistent") is None


def test_remove_ping_url_returns_true(pfile):
    set_ping_url(pfile, "job1", "http://example.com/1")
    assert remove_ping_url(pfile, "job1") is True
    assert get_ping_url(pfile, "job1") is None


def test_remove_ping_url_missing_returns_false(pfile):
    assert remove_ping_url(pfile, "ghost") is False


def test_send_ping_success():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert send_ping("http://example.com/ping") is True


def test_send_ping_failure():
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        assert send_ping("http://example.com/ping") is False


def test_ping_job_no_url_configured(pfile):
    assert ping_job(pfile, "unconfigured") is None


def test_ping_job_sends_ping(pfile):
    set_ping_url(pfile, "job1", "http://example.com/ping")
    with patch("cronwrap.ping.send_ping", return_value=True) as mock_send:
        result = ping_job(pfile, "job1")
    assert result is True
    mock_send.assert_called_once_with("http://example.com/ping", method="GET", timeout=10)
