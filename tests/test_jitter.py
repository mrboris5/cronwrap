"""Tests for cronwrap.jitter"""
import pytest
from unittest.mock import patch
from cronwrap.jitter import _parse_seconds, jitter_seconds, apply_jitter, jitter_reason


def test_parse_seconds_s():
    assert _parse_seconds('30s') == 30.0


def test_parse_seconds_m():
    assert _parse_seconds('2m') == 120.0


def test_parse_seconds_h():
    assert _parse_seconds('1h') == 3600.0


def test_parse_seconds_invalid():
    with pytest.raises(ValueError, match="Invalid duration"):
        _parse_seconds('10d')


def test_jitter_seconds_within_range():
    for _ in range(20):
        val = jitter_seconds('10s')
        assert 0.0 <= val <= 10.0


def test_jitter_seconds_zero():
    val = jitter_seconds('0s')
    assert val == 0.0


def test_jitter_seconds_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        # patch _parse_seconds to return negative
        with patch('cronwrap.jitter._parse_seconds', return_value=-1.0):
            jitter_seconds('1s')


def test_apply_jitter_dry_run_returns_delay():
    delay = apply_jitter('5s', dry_run=True)
    assert 0.0 <= delay <= 5.0


def test_apply_jitter_calls_sleep():
    with patch('cronwrap.jitter.time.sleep') as mock_sleep:
        delay = apply_jitter('2s')
        mock_sleep.assert_called_once_with(delay)


def test_jitter_reason_no_slept():
    msg = jitter_reason('30s')
    assert '30.0s' in msg
    assert 'may be applied' in msg


def test_jitter_reason_with_slept():
    msg = jitter_reason('30s', slept=12.5)
    assert '12.50s' in msg
    assert '30.0s' in msg
    assert 'slept' in msg
