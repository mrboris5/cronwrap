"""Tests for cronwrap.note_cli."""
import pytest
from pathlib import Path

from cronwrap.note_cli import build_note_parser, note_main


@pytest.fixture
def nf(tmp_path):
    return tmp_path / "notes.json"


def _run(nf, *args):
    return note_main(["--file", str(nf)] + list(args))


def test_build_note_parser_returns_parser():
    p = build_note_parser()
    assert p is not None


def test_no_subcommand_returns_1(nf):
    assert note_main(["--file", str(nf)]) == 1


def test_add_exits_0(nf):
    assert _run(nf, "add", "job1", "some text") == 0


def test_add_persists_note(nf):
    _run(nf, "add", "job1", "my note")
    from cronwrap.note import get_notes
    assert get_notes("job1", path=nf) == ["my note"]


def test_list_exits_0_empty(nf, capsys):
    rc = _run(nf, "list", "job1")
    assert rc == 0
    out = capsys.readouterr().out
    assert "No notes" in out


def test_list_shows_notes(nf, capsys):
    _run(nf, "add", "job1", "alpha")
    _run(nf, "add", "job1", "beta")
    _run(nf, "list", "job1")
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_remove_exits_0(nf):
    _run(nf, "add", "job1", "to remove")
    assert _run(nf, "remove", "job1", "0") == 0


def test_remove_bad_index_returns_1(nf):
    _run(nf, "add", "job1", "only")
    assert _run(nf, "remove", "job1", "99") == 1


def test_clear_exits_0(nf):
    _run(nf, "add", "job1", "note")
    assert _run(nf, "clear", "job1") == 0


def test_clear_removes_all(nf):
    _run(nf, "add", "job1", "n1")
    _run(nf, "add", "job1", "n2")
    _run(nf, "clear", "job1")
    from cronwrap.note import get_notes
    assert get_notes("job1", path=nf) == []
