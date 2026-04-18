"""Tests for the CLI entry point."""
import pytest
from unittest.mock import patch, MagicMock

from cronwrap.cli import build_parser, main
from cronwrap.runner import RunResult


def make_result(success=True, returncode=0, stdout="ok", stderr="", duration=0.1):
    r = RunResult(success=success, returncode=returncode, stdout=stdout, stderr=stderr, duration=duration)
    return r


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["echo", "hello"])
    assert args.config is None
    assert args.retries is None
    assert args.timeout is None


def test_build_parser_flags():
    parser = build_parser()
    args = parser.parse_args(["-r", "3", "-t", "60", "--log-level", "DEBUG", "echo"])
    assert args.retries == 3
    assert args.timeout == 60
    assert args.log_level == "DEBUG"


def test_main_no_command_returns_1():
    result = main([])
    assert result == 1


@patch("cronwrap.cli.send_alert")
@patch("cronwrap.cli.run_command")
def test_main_successful_command(mock_run, mock_alert):
    mock_run.return_value = make_result(success=True)
    rc = main(["echo", "hello"])
    assert rc == 0
    mock_run.assert_called_once()


@patch("cronwrap.cli.send_alert")
@patch("cronwrap.cli.run_command")
def test_main_failed_command_returns_1(mock_run, mock_alert):
    mock_run.return_value = make_result(success=False, returncode=1)
    rc = main(["false"])
    assert rc == 1


@patch("cronwrap.cli.send_alert")
@patch("cronwrap.cli.run_command")
def test_main_passes_retries_and_timeout(mock_run, mock_alert):
    mock_run.return_value = make_result()
    main(["-r", "2", "-t", "30", "echo", "hi"])
    _, kwargs = mock_run.call_args
    assert kwargs.get("retries") == 2
    assert kwargs.get("timeout") == 30


@patch("cronwrap.cli.send_alert")
@patch("cronwrap.cli.run_command")
@patch("cronwrap.cli.from_file")
def test_main_loads_config_file(mock_from_file, mock_run, mock_alert, tmp_path):
    from cronwrap.config import Config
    mock_from_file.return_value = Config()
    mock_run.return_value = make_result()
    main(["-c", "some_config.yaml", "echo"])
    mock_from_file.assert_called_once_with("some_config.yaml")


@patch("cronwrap.cli.send_alert")
@patch("cronwrap.cli.run_command")
def test_main_strips_double_dash_separator(mock_run, mock_alert):
    mock_run.return_value = make_result()
    main(["--", "echo", "hello"])
    cmd_arg = mock_run.call_args[0][0]
    assert "--" not in cmd_arg
