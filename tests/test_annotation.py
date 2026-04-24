"""Tests for cronwrap.annotation and annotation_cli."""

import json
import pytest
from pathlib import Path

from cronwrap.annotation import (
    load_annotations,
    save_annotations,
    add_annotation,
    remove_annotation,
    get_annotations,
    clear_annotations,
    list_annotated_jobs,
)
from cronwrap.annotation_cli import build_annotation_parser, annotation_main


@pytest.fixture
def afile(tmp_path):
    return str(tmp_path / "annotations.json")


# --- annotation module ---

def test_load_annotations_missing_file(afile):
    assert load_annotations(afile) == {}


def test_load_annotations_corrupt_file(afile):
    Path(afile).write_text("not json")
    assert load_annotations(afile) == {}


def test_save_and_load_roundtrip(afile):
    data = {"job1": ["note a", "note b"]}
    save_annotations(data, afile)
    assert load_annotations(afile) == data


def test_add_annotation_creates_entry(afile):
    notes = add_annotation("job1", "first note", path=afile)
    assert notes == ["first note"]


def test_add_annotation_appends(afile):
    add_annotation("job1", "note 1", path=afile)
    notes = add_annotation("job1", "note 2", path=afile)
    assert notes == ["note 1", "note 2"]


def test_add_annotation_strips_whitespace(afile):
    notes = add_annotation("job1", "  trimmed  ", path=afile)
    assert notes == ["trimmed"]


def test_add_annotation_empty_raises(afile):
    with pytest.raises(ValueError):
        add_annotation("job1", "   ", path=afile)


def test_get_annotations_missing_job(afile):
    assert get_annotations("ghost", path=afile) == []


def test_get_annotations_returns_notes(afile):
    add_annotation("job1", "hello", path=afile)
    assert get_annotations("job1", path=afile) == ["hello"]


def test_remove_annotation_valid_index(afile):
    add_annotation("job1", "a", path=afile)
    add_annotation("job1", "b", path=afile)
    remaining = remove_annotation("job1", 0, path=afile)
    assert remaining == ["b"]


def test_remove_annotation_invalid_index_raises(afile):
    add_annotation("job1", "only", path=afile)
    with pytest.raises(IndexError):
        remove_annotation("job1", 5, path=afile)


def test_clear_annotations(afile):
    add_annotation("job1", "x", path=afile)
    clear_annotations("job1", path=afile)
    assert get_annotations("job1", path=afile) == []


def test_list_annotated_jobs(afile):
    add_annotation("job1", "note", path=afile)
    add_annotation("job2", "note", path=afile)
    jobs = list_annotated_jobs(path=afile)
    assert set(jobs) == {"job1", "job2"}


def test_list_annotated_jobs_excludes_empty(afile):
    add_annotation("job1", "note", path=afile)
    clear_annotations("job1", path=afile)
    assert list_annotated_jobs(path=afile) == []


# --- annotation_cli ---

def _run(args, afile):
    return annotation_main(["--file", afile] + args)


def test_build_annotation_parser_returns_parser():
    p = build_annotation_parser()
    assert p is not None


def test_no_subcommand_returns_1(afile):
    assert annotation_main(["--file", afile]) == 1


def test_cli_add_exits_0(afile):
    assert _run(["add", "job1", "my note"], afile) == 0


def test_cli_list_exits_0(afile):
    _run(["add", "job1", "note"], afile)
    assert _run(["list", "job1"], afile) == 0


def test_cli_remove_exits_0(afile):
    _run(["add", "job1", "note"], afile)
    assert _run(["remove", "job1", "0"], afile) == 0


def test_cli_remove_bad_index_returns_1(afile):
    _run(["add", "job1", "note"], afile)
    assert _run(["remove", "job1", "99"], afile) == 1


def test_cli_clear_exits_0(afile):
    _run(["add", "job1", "note"], afile)
    assert _run(["clear", "job1"], afile) == 0


def test_cli_jobs_exits_0(afile):
    assert _run(["jobs"], afile) == 0
