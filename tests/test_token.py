"""Tests for cronwrap.token"""

import json
import time
import pytest
from pathlib import Path

from cronwrap.token import (
    load_tokens,
    save_tokens,
    refill,
    consume_token,
    available_tokens,
    reset_tokens,
)


@pytest.fixture
def tfile(tmp_path):
    return str(tmp_path / "tokens.json")


def test_load_tokens_missing_file(tfile):
    assert load_tokens(tfile) == {}


def test_load_tokens_corrupt_file(tfile):
    Path(tfile).write_text("not json")
    assert load_tokens(tfile) == {}


def test_save_and_load_roundtrip(tfile):
    data = {"job1": {"tokens": 5.0, "last_refill": time.time()}}
    save_tokens(tfile, data)
    loaded = load_tokens(tfile)
    assert "job1" in loaded
    assert loaded["job1"]["tokens"] == 5.0


def test_refill_adds_tokens():
    now = time.time()
    entry = {"tokens": 0.0, "last_refill": now - 5.0}
    result = refill(entry, rate=1.0, capacity=10.0)
    assert result["tokens"] >= 4.9
    assert result["tokens"] <= 10.0


def test_refill_does_not_exceed_capacity():
    now = time.time()
    entry = {"tokens": 9.0, "last_refill": now - 100.0}
    result = refill(entry, rate=1.0, capacity=10.0)
    assert result["tokens"] == 10.0


def test_consume_token_success(tfile):
    result = consume_token(tfile, "job1", rate=1.0, capacity=10.0)
    assert result is True
    data = load_tokens(tfile)
    assert data["job1"]["tokens"] < 10.0


def test_consume_token_depleted(tfile):
    # Force empty bucket
    save_tokens(tfile, {"job1": {"tokens": 0.0, "last_refill": time.time()}})
    result = consume_token(tfile, "job1", rate=0.0, capacity=10.0)
    assert result is False


def test_available_tokens_full_bucket(tfile):
    t = available_tokens(tfile, "new_job", rate=1.0, capacity=5.0)
    assert t == 5.0


def test_available_tokens_does_not_consume(tfile):
    available_tokens(tfile, "job1", rate=1.0, capacity=10.0)
    available_tokens(tfile, "job1", rate=1.0, capacity=10.0)
    t = available_tokens(tfile, "job1", rate=1.0, capacity=10.0)
    assert t >= 9.9  # no consumption happened


def test_reset_tokens(tfile):
    save_tokens(tfile, {"job1": {"tokens": 1.0, "last_refill": time.time()}})
    reset_tokens(tfile, "job1", capacity=8.0)
    data = load_tokens(tfile)
    assert data["job1"]["tokens"] == 8.0
