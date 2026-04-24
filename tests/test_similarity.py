"""Tests for cronwrap.similarity."""

import json
import pytest
from pathlib import Path

from cronwrap.similarity import (
    _fingerprint,
    _token_set,
    jaccard,
    store_baseline,
    get_baseline,
    compare_output,
    similarity_reason,
)


@pytest.fixture()
def sim_file(tmp_path):
    return str(tmp_path / "similarity.json")


# --- unit helpers ---

def test_token_set_basic():
    assert _token_set("Hello World") == {"hello", "world"}


def test_token_set_empty():
    assert _token_set("") == set()


def test_fingerprint_order_independent():
    a = _fingerprint("line1\nline2")
    b = _fingerprint("line2\nline1")
    assert a == b


def test_fingerprint_different_content():
    assert _fingerprint("abc") != _fingerprint("xyz")


def test_jaccard_identical():
    assert jaccard("foo bar baz", "foo bar baz") == 1.0


def test_jaccard_disjoint():
    assert jaccard("foo bar", "baz qux") == 0.0


def test_jaccard_partial():
    score = jaccard("foo bar baz", "foo bar qux")
    assert 0.0 < score < 1.0


def test_jaccard_both_empty():
    assert jaccard("", "") == 1.0


# --- store / get ---

def test_store_baseline_creates_entry(sim_file):
    fp = store_baseline("job1", "output text", path=sim_file)
    assert isinstance(fp, str) and len(fp) == 64
    data = json.loads(Path(sim_file).read_text())
    assert "job1" in data


def test_get_baseline_missing_job(sim_file):
    assert get_baseline("nope", path=sim_file) is None


def test_get_baseline_returns_dict(sim_file):
    store_baseline("job2", "hello world", path=sim_file)
    entry = get_baseline("job2", path=sim_file)
    assert entry is not None
    assert "fingerprint" in entry and "sample" in entry


# --- compare_output ---

def test_compare_no_baseline(sim_file):
    result = compare_output("unknown", "some output", path=sim_file)
    assert result["baseline_found"] is False
    assert result["similar"] is True


def test_compare_similar_output(sim_file):
    text = "backup completed successfully 100 files processed"
    store_baseline("bkp", text, path=sim_file)
    result = compare_output("bkp", text, threshold=0.8, path=sim_file)
    assert result["similar"] is True
    assert result["score"] == 1.0


def test_compare_dissimilar_output(sim_file):
    store_baseline("bkp2", "foo bar baz", path=sim_file)
    result = compare_output("bkp2", "completely different content xyz", threshold=0.9, path=sim_file)
    assert result["similar"] is False
    assert result["score"] < 0.9


# --- similarity_reason ---

def test_reason_no_baseline(sim_file):
    msg = similarity_reason("ghost", "output", path=sim_file)
    assert "no baseline" in msg


def test_reason_similar(sim_file):
    store_baseline("j", "the quick brown fox", path=sim_file)
    msg = similarity_reason("j", "the quick brown fox", path=sim_file)
    assert "similar" in msg


def test_reason_differs(sim_file):
    store_baseline("j2", "alpha beta gamma", path=sim_file)
    msg = similarity_reason("j2", "completely unrelated zzz", threshold=0.9, path=sim_file)
    assert "differs" in msg
