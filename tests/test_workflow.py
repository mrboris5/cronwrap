"""Tests for cronwrap.workflow."""
import json
import pytest
from cronwrap.workflow import (
    load_workflows, save_workflows, register_workflow,
    get_workflow, remove_workflow, list_workflows, workflow_step_index
)


@pytest.fixture
def wfile(tmp_path):
    return str(tmp_path / "workflows.json")


def test_load_workflows_missing_file(wfile):
    assert load_workflows(wfile) == {}


def test_load_workflows_corrupt_file(wfile, tmp_path):
    (tmp_path / "workflows.json").write_text("not-json")
    assert load_workflows(wfile) == {}


def test_save_and_load_roundtrip(wfile):
    data = {"wf1": {"workflow_id": "wf1", "steps": ["a", "b"], "description": ""}}
    save_workflows(wfile, data)
    assert load_workflows(wfile) == data


def test_register_workflow_creates_entry(wfile):
    wf = register_workflow(wfile, "deploy", ["build", "test", "push"])
    assert wf["workflow_id"] == "deploy"
    assert wf["steps"] == ["build", "test", "push"]


def test_register_workflow_persists(wfile):
    register_workflow(wfile, "deploy", ["build", "push"])
    assert get_workflow(wfile, "deploy") is not None


def test_register_workflow_with_description(wfile):
    wf = register_workflow(wfile, "ci", ["lint", "test"], description="CI pipeline")
    assert wf["description"] == "CI pipeline"


def test_register_workflow_overwrites(wfile):
    register_workflow(wfile, "wf", ["a"])
    register_workflow(wfile, "wf", ["a", "b"])
    assert get_workflow(wfile, "wf")["steps"] == ["a", "b"]


def test_get_workflow_missing(wfile):
    assert get_workflow(wfile, "no-such") is None


def test_remove_workflow_returns_true(wfile):
    register_workflow(wfile, "wf", ["a"])
    assert remove_workflow(wfile, "wf") is True


def test_remove_workflow_absent_returns_false(wfile):
    assert remove_workflow(wfile, "ghost") is False


def test_remove_workflow_deletes_entry(wfile):
    register_workflow(wfile, "wf", ["a"])
    remove_workflow(wfile, "wf")
    assert get_workflow(wfile, "wf") is None


def test_list_workflows_empty(wfile):
    assert list_workflows(wfile) == []


def test_list_workflows_returns_all(wfile):
    register_workflow(wfile, "wf1", ["a"])
    register_workflow(wfile, "wf2", ["b"])
    ids = {w["workflow_id"] for w in list_workflows(wfile)}
    assert ids == {"wf1", "wf2"}


def test_workflow_step_index_found(wfile):
    register_workflow(wfile, "wf", ["alpha", "beta", "gamma"])
    assert workflow_step_index(wfile, "wf", "beta") == 1


def test_workflow_step_index_not_found(wfile):
    register_workflow(wfile, "wf", ["alpha"])
    assert workflow_step_index(wfile, "wf", "delta") == -1


def test_workflow_step_index_missing_workflow(wfile):
    assert workflow_step_index(wfile, "ghost", "step") == -1
