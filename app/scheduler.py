"""Tinh toan chu ky quet, dam bao khong vuot rate limit cua Threads API."""

import math

# Threads keyword_search: toi da 2200 query / 24h / user (rolling window).
DAILY_QUERY_LIMIT = 2200
MINUTES_PER_DAY = 1440
# Chua ~10% bien an toan de tranh cham tran do thoi diem.
SAFE_MARGIN_FACTOR = 0.9
DEFAULT_POLL_MINUTES = 5


def compute_poll_interval(
    keyword_count: int,
    explicit_minutes: int | None = None,
) -> int:
    """Tinh chu ky quet (phut).

    Moi chu ky quet toan bo tu khoa 1 lan => queries/ngay =
    keyword_count * (1440 / interval). Chon interval nho nhat ma van
    duoi gioi han an toan.

    Neu nguoi dung dat cuong (explicit_minutes), dung gia tri do.
    """
    if explicit_minutes is not None:
        return max(1, explicit_minutes)
    if keyword_count <= 0:
        return DEFAULT_POLL_MINUTES

    interval = math.ceil(
        MINUTES_PER_DAY * keyword_count / (DAILY_QUERY_LIMIT * SAFE_MARGIN_FACTOR)
    )
    return max(1, interval)
