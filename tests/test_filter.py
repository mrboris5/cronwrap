"""Tests for cronwrap.filter module."""

import pytest
from cronwrap.filter import redact, truncate_lines, truncate_bytes, filter_output


def test_redact_password():
    line = "password=supersecret123"
    result = redact(line)
    assert "supersecret123" not in result
    assert "[REDACTED]" in result


def test_redact_token():
    line = "token: ghp_abcdef1234567890"
    result = redact(line)
    assert "ghp_abcdef1234567890" not in result
    assert "[REDACTED]" in result


def test_redact_leaves_normal_text():
    line = "everything looks fine here"
    assert redact(line) == line


def test_truncate_lines_no_truncation():
    text = "\n".join([f"line {i}" for i in range(10)])
    result = truncate_lines(text, max_lines=20)
    assert result == text


def test_truncate_lines_truncates():
    lines = [f"line {i}" for i in range(300)]
    text = "\n".join(lines)
    result = truncate_lines(text, max_lines=200)
    assert "truncated" in result
    assert "line 299" in result
    assert "line 0" not in result


def test_truncate_lines_keeps_last_n():
    lines = [f"{i}" for i in range(50)]
    text = "\n".join(lines)
    result = truncate_lines(text, max_lines=10)
    result_lines = [l for l in result.splitlines() if not l.startswith('[')]
    assert result_lines[-1] == "49"
    assert len(result_lines) == 10


def test_truncate_bytes_no_truncation():
    text = "hello world"
    assert truncate_bytes(text, max_bytes=1024) == text


def test_truncate_bytes_truncates():
    text = "a" * 200
    result = truncate_bytes(text, max_bytes=100)
    assert len(result.encode("utf-8")) > 100  # includes notice
    assert "truncated" in result
    assert result.startswith("a" * 100)


def test_filter_output_combines_all():
    lines = [f"line {i}" for i in range(300)]
    lines.append("api_key=topsecret")
    text = "\n".join(lines)
    result = filter_output(text, max_lines=200, redact_secrets=True)
    assert "topsecret" not in result
    assert "[REDACTED]" in result
    assert "truncated" in result


def test_filter_output_no_redact():
    text = "password=visible"
    result = filter_output(text, redact_secrets=False)
    assert "visible" in result
