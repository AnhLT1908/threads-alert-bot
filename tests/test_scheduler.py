"""Test tinh toan chu ky quet."""

from app.scheduler import compute_poll_interval


def test_six_keywords_defaults_to_five_minutes():
    assert compute_poll_interval(6) == 5


def test_more_keywords_widens_interval():
    # 20 tu khoa: 20*1440/1980 = 14.54 -> 15 phut
    assert compute_poll_interval(20) == 15
    # 10 tu khoa: 10*1440/1980 = 7.27 -> 8 phut
    assert compute_poll_interval(10) == 8


def test_single_keyword_can_poll_every_minute():
    assert compute_poll_interval(1) == 1


def test_zero_keywords_uses_default():
    assert compute_poll_interval(0) == 5


def test_explicit_interval_overrides_calculation():
    assert compute_poll_interval(100, explicit_minutes=2) == 2


def test_explicit_interval_never_below_one():
    assert compute_poll_interval(6, explicit_minutes=0) == 1
