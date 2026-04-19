"""Tests for cronwrap.backoff."""
import pytest
from cronwrap.backoff import backoff_delays, next_delay


def test_backoff_delays_count():
    delays = list(backoff_delays(base=1.0, factor=2.0, max_delay=60.0, jitter=False, max_retries=4))
    assert len(delays) == 4


def test_backoff_delays_no_jitter_values():
    delays = list(backoff_delays(base=1.0, factor=2.0, max_delay=100.0, jitter=False, max_retries=5))
    assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]


def test_backoff_delays_capped_at_max():
    delays = list(backoff_delays(base=1.0, factor=10.0, max_delay=5.0, jitter=False, max_retries=4))
    for d in delays:
        assert d <= 5.0


def test_backoff_delays_jitter_within_bounds():
    delays = list(backoff_delays(base=1.0, factor=2.0, max_delay=50.0, jitter=True, max_retries=20))
    for d in delays:
        assert 0.0 <= d <= 50.0


def test_backoff_delays_invalid_base():
    with pytest.raises(ValueError, match="base"):
        list(backoff_delays(base=0))


def test_backoff_delays_invalid_factor():
    with pytest.raises(ValueError, match="factor"):
        list(backoff_delays(factor=0.5))


def test_backoff_delays_invalid_max_delay():
    with pytest.raises(ValueError, match="max_delay"):
        list(backoff_delays(base=10.0, max_delay=5.0))


def test_next_delay_attempt_zero():
    assert next_delay(0, base=2.0, factor=3.0, max_delay=100.0) == 2.0


def test_next_delay_grows_exponentially():
    d0 = next_delay(0, base=1.0, factor=2.0, max_delay=1000.0)
    d1 = next_delay(1, base=1.0, factor=2.0, max_delay=1000.0)
    d2 = next_delay(2, base=1.0, factor=2.0, max_delay=1000.0)
    assert d1 == d0 * 2
    assert d2 == d0 * 4


def test_next_delay_capped():
    d = next_delay(10, base=1.0, factor=2.0, max_delay=10.0)
    assert d == 10.0


def test_next_delay_negative_attempt():
    with pytest.raises(ValueError, match="attempt"):
        next_delay(-1)


def test_next_delay_jitter_within_bounds():
    for _ in range(50):
        d = next_delay(3, base=1.0, factor=2.0, max_delay=100.0, jitter=True)
        assert 0.0 <= d <= 8.0
