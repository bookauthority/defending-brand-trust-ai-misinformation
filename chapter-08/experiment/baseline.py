from __future__ import annotations

from typing import Dict, List

from .utils import WeeklyBucket, build_weekly_buckets, mean


def build_baseline_weekly_summary(data: Dict[str, object]) -> List[Dict[str, float]]:
    """Aggregate synthetic data into a simple weekly table.

    This represents the baseline: flat reporting with basic counts and averages.
    """

    days = data["time_index"]
    sentiment = data["sentiment"]
    web = data["web"]
    financial = data["financial"]

    buckets = build_weekly_buckets(days)
    weekly: List[Dict[str, float]] = []

    # Build index maps for quick lookup
    # Each list is aligned with `days` indices
    sent_by_day = {i: [] for i in range(len(days))}
    for rec in sentiment:
        # sentiment list is in day-major order, 4 channels per day
        # Use index via position; here we compute from day difference
        idx = (rec.day - days[0]).days
        sent_by_day.setdefault(idx, []).append(rec)

    web_by_day = {i: None for i in range(len(days))}
    for rec in web:
        idx = (rec.day - days[0]).days
        web_by_day[idx] = rec

    fin_by_day = {i: None for i in range(len(days))}
    for rec in financial:
        idx = (rec.day - days[0]).days
        fin_by_day[idx] = rec

    for bucket in buckets:
        sentiments = []
        volumes = []
        revenues = []
        for idx in bucket.indices:
            s_list = sent_by_day.get(idx, [])
            for s in s_list:
                sentiments.append(s.sentiment)
                volumes.append(s.volume)
            _ = web_by_day.get(idx)
            f = fin_by_day.get(idx)
            if f is not None:
                revenues.append(f.revenue)
        if not bucket.indices:
            continue
        weekly.append(
            {
                "week_start_ordinal": float(bucket.start_date.toordinal()),
                "avg_sentiment": float(mean(sentiments) if sentiments else 0.0),
                "total_posts": float(sum(volumes) if volumes else 0.0),
                "revenue": float(mean(revenues) if revenues else 0.0),
            }
        )

    return weekly
