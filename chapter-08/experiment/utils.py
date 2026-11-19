from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Sequence


def daterange(start: date, end: date) -> List[date]:
    """Return a list of dates from start to end inclusive."""

    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur = cur + timedelta(days=1)
    return days


def week_index(start: date, days: Sequence[date]) -> Dict[int, List[int]]:
    """Map ISO week numbers (relative offset) to indices in `days`.

    Weeks are numbered from 0 upward starting at the first day.
    """

    if not days:
        return {}
    mapping: Dict[int, List[int]] = {}
    base_iso_year, base_iso_week, _ = start.isocalendar()
    for idx, d in enumerate(days):
        year, wk, _ = d.isocalendar()
        offset = (year - base_iso_year) * 54 + (wk - base_iso_week)
        mapping.setdefault(offset, []).append(idx)
    return mapping


def mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def median(values: Sequence[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return float((s[mid - 1] + s[mid]) / 2.0)


def pearson_correlation(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Compute a simple Pearson correlation coefficient.

    Returns None if insufficient variance or length.
    """

    n = len(xs)
    if n == 0 or n != len(ys):
        return None
    mx = mean(xs)
    my = mean(ys)
    num = 0.0
    sx = 0.0
    sy = 0.0
    for x, y in zip(xs, ys):
        dx = x - mx
        dy = y - my
        num += dx * dy
        sx += dx * dx
        sy += dy * dy
    if sx == 0.0 or sy == 0.0:
        return None
    return float(num / (sx ** 0.5 * sy ** 0.5))


@dataclass
class WeeklyBucket:
    start_date: date
    indices: List[int]


def build_weekly_buckets(days: Sequence[date]) -> List[WeeklyBucket]:
    if not days:
        return []
    mapping = week_index(days[0], days)
    buckets: List[WeeklyBucket] = []
    for offset in sorted(mapping.keys()):
        idxs = mapping[offset]
        buckets.append(WeeklyBucket(start_date=days[idxs[0]], indices=idxs))
    return buckets
