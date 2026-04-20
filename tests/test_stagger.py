"""Tests for cronwrap.stagger module."""

import pytest
from datetime import datetime, timedelta

from cronwrap.stagger import (
    _parse_seconds,
    stagger_offset,
    stagger_start,
    stagger_reason,
)


# --- _parse_seconds ---

def test_parse_seconds_s():
    assert _parse_seconds('45s') == 45


def test_parse_seconds_m():
    assert _parse_seconds('5m') == 300


def test_parse_seconds_h():
    assert _parse_seconds('2h') == 7200


def test_parse_seconds_invalid():
    with pytest.raises(ValueError, match='Invalid duration'):
        _parse_seconds('10d')


# --- stagger_offset ---

def test_stagger_offset_within_window():
    offset = stagger_offset('job-abc', '10m')
    assert 0 <= offset < 600


def test_stagger_offset_deterministic():
    o1 = stagger_offset('job-xyz', '5m')
    o2 = stagger_offset('job-xyz', '5m')
    assert o1 == o2


def test_stagger_offset_different_jobs_differ():
    o1 = stagger_offset('job-alpha', '10m')
    o2 = stagger_offset('job-beta', '10m')
    # Not guaranteed but overwhelmingly likely with different hashes
    assert o1 != o2


def test_stagger_offset_multi_job_within_window():
    window = '10m'
    for i in range(5):
        offset = stagger_offset(f'job-{i}', window, total_jobs=5, index=i)
        assert 0 <= offset < 600


def test_stagger_offset_multi_job_spread():
    """Jobs with different indices should not all land in the same slot."""
    offsets = [
        stagger_offset('job', '10m', total_jobs=5, index=i)
        for i in range(5)
    ]
    # With 5 slots of 120s each, offsets should span multiple slots
    assert max(offsets) - min(offsets) > 0


# --- stagger_start ---

def test_stagger_start_after_now():
    now = datetime(2024, 1, 15, 12, 0, 0)
    start = stagger_start('job-1', '10m', now=now)
    assert start >= now


def test_stagger_start_within_window():
    now = datetime(2024, 1, 15, 12, 0, 0)
    start = stagger_start('job-1', '10m', now=now)
    assert start <= now + timedelta(minutes=10)


def test_stagger_start_defaults_to_utcnow():
    before = datetime.utcnow()
    start = stagger_start('job-1', '5m')
    after = datetime.utcnow()
    assert before <= start <= after + timedelta(minutes=5)


# --- stagger_reason ---

def test_stagger_reason_contains_job_id():
    reason = stagger_reason('my-job', '5m')
    assert 'my-job' in reason


def test_stagger_reason_contains_window():
    reason = stagger_reason('my-job', '5m')
    assert '5m' in reason


def test_stagger_reason_minutes_format():
    # Force an offset >= 60s by using a large window
    reason = stagger_reason('job-abc', '1h')
    # Should mention minutes or seconds
    assert 'm' in reason or 's' in reason


def test_stagger_reason_seconds_only_format():
    # Use a tiny window so offset < 60
    reason = stagger_reason('job-abc', '30s')
    assert 's' in reason
