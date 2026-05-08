"""Tests for cronwrap.workflow_cli."""
import pytest
from cronwrap.workflow_cli import build_workflow_parser, workflow_main


@pytest.fixture
def wf(tmp_path):
    return str(tmp_path / "workflows.json")


def _run(wf_path, *args):
    return workflow_main(["--file", wf_path] + list(args))


def test_build_workflow_parser_returns_parser():
    p = build_workflow_parser()
    assert p is not None


def test_no_subcommand_returns_1(wf):
    assert _run(wf) == 1


def test_register_exits_0(wf):
    assert _run(wf, "register", "deploy", "build", "push") == 0


def test_register_with_description(wf):
    rc = _run(wf, "register", "ci", "lint", "test",
              "--description", "CI pipeline")
    assert rc == 0


def test_show_exits_0(wf):
    _run(wf, "register", "deploy", "build", "push")
    assert _run(wf, "show", "deploy") == 0


def test_show_missing_exits_1(wf):
    assert _run(wf, "show", "ghost") == 1


def test_remove_exits_0(wf):
    _run(wf, "register", "deploy", "build")
    assert _run(wf, "remove", "deploy") == 0


def test_remove_missing_exits_1(wf):
    assert _run(wf, "remove", "ghost") == 1


def test_list_empty_exits_0(wf):
    assert _run(wf, "list") == 0


def test_list_with_entries_exits_0(wf):
    _run(wf, "register", "wf1", "a", "b")
    _run(wf, "register", "wf2", "c")
    assert _run(wf, "list") == 0
