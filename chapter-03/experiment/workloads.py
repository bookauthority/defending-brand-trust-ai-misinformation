from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class Event:
    event_id: str
    timestamp: datetime
    channel: str  # 'social','search','dark_web','owned'
    source_id: str
    content_text: str
    author_reputation_score: float
    engagement_count: int
    is_ground_truth_misinfo: bool
    misinfo_cluster_id: Optional[str]
    human_label_decision: str
    true_narrative_start: bool = False
    bot_likelihood_score: Optional[float] = None


BASE_TIME = datetime(2024, 1, 1, 0, 0, 0)


def _make_id(prefix: str, index: int) -> str:
    return f"{prefix}_{index:05d}"


def generate_wl1() -> List[Event]:
    """WL1_Synthetic_SlowBurn_Deepfake_Rumor.

    Gradual increase from ~10 to ~300 events/hour over 24 hours.
    Misinfo 5–15% of content; starts on dark_web, then social, then owned.
    """

    events: List[Event] = []
    event_index = 0
    hours = 24
    total_events = 0
    for h in range(hours):
        # linear growth from 10 to 300
        per_hour = int(10 + (290 * h / (hours - 1)))
        total_events += per_hour
        for i in range(per_hour):
            ts = BASE_TIME + timedelta(hours=h, minutes=(i * 60 / max(per_hour, 1)))
            # channel distribution phases
            if h < 8:
                channel = "dark_web" if i % 5 != 0 else "social"
            elif h < 16:
                channel = "social" if i % 4 != 0 else "search"
            else:
                if i % 5 == 0:
                    channel = "owned"
                else:
                    channel = "social" if i % 2 == 0 else "search"

            is_misinfo = False
            cluster_id: Optional[str] = None
            true_start = False

            # misinfo cluster: 10% of events, banded by index
            if (i % 10) == 0 and 2 <= h <= 18:
                is_misinfo = True
                cluster_id = "deepfake_exec_v1"
                true_start = h <= 3 and i < 30

            # content text marker for keyword rules
            if is_misinfo:
                text = "BrandX fake video leak scandal about CEO"
            else:
                text = "Generic chatter about BrandX product and service experience"

            human_label = "misinfo" if is_misinfo else "benign"
            ev = Event(
                event_id=_make_id("WL1", event_index),
                timestamp=ts,
                channel=channel,
                source_id=f"src_{channel}_{event_index%50}",
                content_text=text,
                author_reputation_score=0.3 if is_misinfo else 0.7,
                engagement_count=5 if is_misinfo else 2,
                is_ground_truth_misinfo=is_misinfo,
                misinfo_cluster_id=cluster_id,
                human_label_decision=human_label,
                true_narrative_start=true_start,
            )
            events.append(ev)
            event_index += 1
    return events


def generate_wl2() -> List[Event]:
    """WL2_Synthetic_Flash_Boycott_Campaign.

    Abrupt spike from ~50 to >5000 events/hour within 2 hours, then decay.
    """

    events: List[Event] = []
    event_index = 0

    # Pre-spike: 2 hours of ~50 events/hour
    for h in range(2):
        per_hour = 50
        for i in range(per_hour):
            ts = BASE_TIME + timedelta(hours=h, minutes=(i * 60 / per_hour))
            channel = "social" if i % 2 == 0 else "search"
            text = "Normal conversation about BrandX promotions"
            ev = Event(
                event_id=_make_id("WL2", event_index),
                timestamp=ts,
                channel=channel,
                source_id=f"pre_src_{event_index%40}",
                content_text=text,
                author_reputation_score=0.6,
                engagement_count=1,
                is_ground_truth_misinfo=False,
                misinfo_cluster_id=None,
                human_label_decision="benign",
            )
            events.append(ev)
            event_index += 1

    # Spike: 2 hours of 5000 events/hour
    for h in range(2, 4):
        per_hour = 5000
        for i in range(per_hour):
            ts = BASE_TIME + timedelta(hours=h, minutes=(i * 60 / per_hour))
            if i % 20 == 0:
                channel = "owned"
            else:
                channel = "social"
            is_misinfo = (i % 3 == 0)
            bot_score = 0.8 if (i % 5 == 0) else 0.2
            if is_misinfo:
                text = "Boycott BrandX due to fake product safety leak #BrandXBoycott"
            else:
                text = "Discussion of BrandX safety rumors and unrelated chatter"
            human_label = "misinfo" if is_misinfo else "benign"
            ev = Event(
                event_id=_make_id("WL2", event_index),
                timestamp=ts,
                channel=channel,
                source_id=f"spike_src_{event_index%500}",
                content_text=text,
                author_reputation_score=0.4 if is_misinfo else 0.7,
                engagement_count=3 if is_misinfo else 1,
                is_ground_truth_misinfo=is_misinfo,
                misinfo_cluster_id="boycott_fake_safety_v1" if is_misinfo else None,
                human_label_decision=human_label,
                bot_likelihood_score=bot_score,
            )
            events.append(ev)
            event_index += 1

    # Decay: 6 hours from 200 events/hour
    for h in range(4, 10):
        per_hour = 200
        for i in range(per_hour):
            ts = BASE_TIME + timedelta(hours=h, minutes=(i * 60 / per_hour))
            if i % 10 == 0:
                channel = "owned"
            elif i % 3 == 0:
                channel = "search"
            else:
                channel = "social"
            is_misinfo = (i % 7 == 0)
            text = (
                "Questions about BrandX safety reports and boycott posts"
                if is_misinfo
                else "Routine brand inquiries and marketing responses"
            )
            human_label = "misinfo" if is_misinfo else "benign"
            bot_score = 0.6 if (i % 13 == 0) else 0.1
            ev = Event(
                event_id=_make_id("WL2", event_index),
                timestamp=ts,
                channel=channel,
                source_id=f"decay_src_{event_index%200}",
                content_text=text,
                author_reputation_score=0.5,
                engagement_count=2,
                is_ground_truth_misinfo=is_misinfo,
                misinfo_cluster_id="boycott_fake_safety_v1" if is_misinfo else None,
                human_label_decision=human_label,
                bot_likelihood_score=bot_score,
            )
            events.append(ev)
            event_index += 1

    return events


def generate_wl3() -> List[Event]:
    """WL3_Synthetic_Background_Chatter_With_No_Incident.

    24 hours, 200–800 events/hour, no misinfo.
    """

    events: List[Event] = []
    event_index = 0
    for h in range(24):
        # vary between 200 and 800 with a simple wave
        per_hour = 200 + (h % 6) * 100
        for i in range(per_hour):
            ts = BASE_TIME + timedelta(hours=h, minutes=(i * 60 / per_hour))
            # channel mix: 70% social, 20% search, 10% owned
            r = i % 10
            if r < 7:
                channel = "social"
            elif r < 9:
                channel = "search"
            else:
                channel = "owned"
            text = "Background chatter: marketing, support, general news about BrandX"
            ev = Event(
                event_id=_make_id("WL3", event_index),
                timestamp=ts,
                channel=channel,
                source_id=f"bg_src_{event_index%300}",
                content_text=text,
                author_reputation_score=0.6,
                engagement_count=1,
                is_ground_truth_misinfo=False,
                misinfo_cluster_id=None,
                human_label_decision="benign",
            )
            events.append(ev)
            event_index += 1
    return events


WORKLOAD_GENERATORS = {
    "WL1": generate_wl1,
    "WL2": generate_wl2,
    "WL3": generate_wl3,
}
