from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List

from .utils import daterange


CHANNELS = ["twitter", "facebook", "news", "owned"]


@dataclass
class SentimentRecord:
    day: date
    channel: str
    sentiment: float
    volume: int
    misinformation_mentions: int


@dataclass
class IncidentRecord:
    incident_id: str
    type: str
    severity: int
    channel: str
    is_misinformation: bool
    alert_time: datetime
    detection_time: datetime
    classification_time: datetime
    public_statement_time: datetime
    containment_time: datetime
    resolved_time: datetime


@dataclass
class WebRecord:
    day: date
    site_visits: int
    help_center_visits: int
    branded_search_volume: int


@dataclass
class FinancialRecord:
    day: date
    revenue: float
    conversion_rate: float
    churn_rate: float
    nps: float
    call_center_volume: int


def generate_time_index(num_days: int = 730) -> List[date]:
    start = date(2023, 1, 1)
    end = start + timedelta(days=num_days - 1)
    return daterange(start, end)


def generate_incidents(days: List[date], rng: random.Random) -> List[IncidentRecord]:
    incidents: List[IncidentRecord] = []
    if not days:
        return incidents

    # Create a few misinformation incidents spaced over the period
    num = 4
    step = max(10, len(days) // (num + 1))
    for i in range(num):
        idx = (i + 1) * step
        if idx >= len(days):
            idx = len(days) - 1
        d = days[idx]
        # Randomly assign hour offsets
        alert = datetime(d.year, d.month, d.day, 8, 0)
        detect_offset = rng.randint(1, 10)
        detect = alert + timedelta(hours=detect_offset)
        class_offset = detect_offset + rng.randint(1, 6)
        classification = alert + timedelta(hours=class_offset)
        statement_offset = class_offset + rng.randint(2, 12)
        statement = alert + timedelta(hours=statement_offset)
        containment_offset = statement_offset + rng.randint(4, 24)
        containment = alert + timedelta(hours=containment_offset)
        resolved_offset = containment_offset + rng.randint(12, 72)
        resolved = alert + timedelta(hours=resolved_offset)

        inc = IncidentRecord(
            incident_id=f"INC_{i+1}",
            type=rng.choice([
                "deepfake_video",
                "fabricated_safety_issue",
                "synthetic_reviews",
            ]),
            severity=rng.randint(1, 5),
            channel=rng.choice(CHANNELS),
            is_misinformation=True,
            alert_time=alert,
            detection_time=detect,
            classification_time=classification,
            public_statement_time=statement,
            containment_time=containment,
            resolved_time=resolved,
        )
        incidents.append(inc)

    return incidents


def _incident_effect_multiplier(day: date, incidents: List[IncidentRecord]) -> float:
    """Return a sentiment multiplier (<1 means worse sentiment) based on incident proximity."""

    factor = 1.0
    for inc in incidents:
        start = inc.alert_time.date()
        end = inc.resolved_time.date()
        if start <= day <= end:
            # Triangular impact: strongest near alert, decays toward resolved
            total_days = (end - start).days + 1
            if total_days <= 0:
                continue
            pos = (day - start).days
            center = total_days / 3.0
            distance = abs(pos - center)
            magnitude = max(0.1, 1.0 - distance / max(1.0, center * 2.0))
            factor -= 0.2 * magnitude
    return max(0.4, factor)


def generate_sentiment(
    days: List[date], incidents: List[IncidentRecord], rng: random.Random
) -> List[SentimentRecord]:
    records: List[SentimentRecord] = []
    for idx, d in enumerate(days):
        base_angle = 2 * math.pi * (idx / 365.0)
        seasonal = 0.1 * math.sin(base_angle)
        incident_mult = _incident_effect_multiplier(d, incidents)
        for ch in CHANNELS:
            channel_bias = {
                "twitter": -0.05,
                "facebook": 0.0,
                "news": -0.02,
                "owned": 0.05,
            }[ch]
            noise = rng.uniform(-0.1, 0.1)
            sentiment = max(
                -1.0,
                min(1.0, (0.5 + seasonal + channel_bias + noise) * incident_mult),
            )
            volume = int(rng.gauss(1000, 100))
            if volume < 100:
                volume = 100
            # Misinformation mentions: higher during incidents and especially in affected channel
            base_mm = rng.randint(0, 5)
            for inc in incidents:
                if inc.alert_time.date() <= d <= inc.resolved_time.date():
                    boost = 5
                    if ch == inc.channel:
                        boost = 10
                    base_mm += rng.randint(0, boost)
            records.append(
                SentimentRecord(
                    day=d,
                    channel=ch,
                    sentiment=sentiment,
                    volume=volume,
                    misinformation_mentions=base_mm,
                )
            )
    return records


def generate_web(
    days: List[date], incidents: List[IncidentRecord], rng: random.Random
) -> List[WebRecord]:
    records: List[WebRecord] = []
    for idx, d in enumerate(days):
        base_visits = 50000 + 1000 * math.sin(2 * math.pi * idx / 365.0)
        help_center = 5000 + 500 * math.cos(2 * math.pi * idx / 180.0)
        branded_search = 20000 + 500 * math.sin(2 * math.pi * idx / 30.0)
        mult = _incident_effect_multiplier(d, incidents)
        # During incidents: more help visits and search, possibly fewer normal visits
        if mult < 1.0:
            help_center *= 1.2
            branded_search *= 1.1
            base_visits *= 0.95
        records.append(
            WebRecord(
                day=d,
                site_visits=int(base_visits + rng.gauss(0, 2000)),
                help_center_visits=int(help_center + rng.gauss(0, 300)),
                branded_search_volume=int(
                    branded_search + rng.gauss(0, 500)
                ),
            )
        )
    return records


def generate_financial(
    days: List[date], incidents: List[IncidentRecord], rng: random.Random
) -> List[FinancialRecord]:
    records: List[FinancialRecord] = []
    for idx, d in enumerate(days):
        base_rev = 1_000_000 + 20_000 * math.sin(2 * math.pi * idx / 365.0)
        conv = 0.04 + 0.005 * math.sin(2 * math.pi * idx / 180.0)
        churn = 0.01 + 0.002 * math.cos(2 * math.pi * idx / 365.0)
        nps = 40 + 5 * math.sin(2 * math.pi * idx / 200.0)
        calls = 800 + 50 * math.cos(2 * math.pi * idx / 90.0)

        mult = _incident_effect_multiplier(d, incidents)
        if mult < 1.0:
            # Incidents: revenue dips, churn and calls rise, NPS drops
            base_rev *= mult
            churn *= 1.2
            calls *= 1.3
            nps -= 5 * (1.0 - mult)
        records.append(
            FinancialRecord(
                day=d,
                revenue=float(base_rev + rng.gauss(0, 50_000)),
                conversion_rate=float(conv + rng.gauss(0, 0.001)),
                churn_rate=float(churn + rng.gauss(0, 0.0005)),
                nps=float(nps + rng.gauss(0, 1.0)),
                call_center_volume=int(calls + rng.gauss(0, 30)),
            )
        )
    return records


def generate_all(seed: int = 42) -> Dict[str, object]:
    """Generate all synthetic datasets and return them in a dict.

    The same function is used for both baseline and treatment conditions,
    with a controllable seed for reproducibility.
    """

    rng = random.Random(seed)
    days = generate_time_index()
    incidents = generate_incidents(days, rng)
    sentiment = generate_sentiment(days, incidents, rng)
    web = generate_web(days, incidents, rng)
    financial = generate_financial(days, incidents, rng)

    return {
        "time_index": days,
        "incidents": incidents,
        "sentiment": sentiment,
        "web": web,
        "financial": financial,
    }
