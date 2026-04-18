import pytest
from unittest.mock import patch
from cronwrap.runner import run_command, RunResult
import subprocess


def test_successful_command():
    result = run_command("echo hello")
    assert result.success
    assert result.returncode == 0
    assert "hello" in result.stdout
    assert result.attempt == 1


def test_failed_command():
    result = run_command("exit 1")
    assert not result.success
    assert result.returncode == 1


def test_duration_is_positive():
    result = run_command("echo ok")
    assert result.duration > 0


def test_retries_on_failure():
    result = run_command("exit 1", retries=2, retry_delay=0)
    assert not result.success
    assert result.attempt == 3


def test_no_retry_on_success():
    result = run_command("echo hi", retries=3, retry_delay=0)
    assert result.success
    assert result.attempt == 1


def test_timeout_returns_failure():
    result = run_command("sleep 10", timeout=1)
    assert not result.success
    assert result.returncode == -1
    assert "timed out" in result.stderr


def test_run_result_fields():
    result = RunResult(
        command="echo test",
        returncode=0,
        stdout="test\n",
        stderr="",
        duration=0.1,
        attempt=1,
    )
    assert result.success
    assert result.command == "echo test"
