"""Tests for cronwrap.label_cli."""
import pytest
from cronwrap.label_cli import label_main, build_label_parser
from cronwrap.label import add_label


@pytest.fixture
def lf(tmp_path):
    return str(tmp_path / "labels.json")


def _run(args, lf):
    return label_main(["--file", lf] + args)


def test_build_label_parser_returns_parser():
    p = build_label_parser()
    assert p is not None


def test_no_subcommand_returns_1(lf):
    assert _run([], lf) == 1


def test_add_label_exits_0(lf):
    assert _run(["add", "job1", "critical"], lf) == 0


def test_add_label_persists(lf):
    _run(["add", "job1", "critical"], lf)
    from cronwrap.label import get_labels
    assert "critical" in get_labels("job1", lf)


def test_remove_label_exits_0(lf):
    _run(["add", "job1", "critical"], lf)
    assert _run(["remove", "job1", "critical"], lf) == 0


def test_list_labels_exits_0(lf, capsys):
    add_label("job1", "nightly", lf)
    rc = _run(["list", "job1"], lf)
    assert rc == 0
    out = capsys.readouterr().out
    assert "nightly" in out


def test_list_labels_empty(lf, capsys):
    _run(["list", "unknown"], lf)
    out = capsys.readouterr().out
    assert "no labels" in out


def test_find_label_exits_0(lf, capsys):
    add_label("job1", "prod", lf)
    rc = _run(["find", "prod"], lf)
    assert rc == 0
    assert "job1" in capsys.readouterr().out


def test_find_label_none(lf, capsys):
    _run(["find", "ghost"], lf)
    assert "none" in capsys.readouterr().out


def test_clear_label_exits_0(lf, capsys):
    add_label("job1", "x", lf)
    rc = _run(["clear", "job1"], lf)
    assert rc == 0
    assert "Cleared" in capsys.readouterr().out
