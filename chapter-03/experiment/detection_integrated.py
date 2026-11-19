from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Set

from .config_loader import DetectionConfig
from .workloads import Event


@dataclass
class IntegratedAlert:
    timestamp: datetime
    event_ids: List[str]
    composite_score: float
    trigger_type: str  # 'heuristic', 'ml', 'fusion', 'human_confirmation'


def _window_start(ts: datetime, window_minutes: int = 15) -> datetime:
    return ts.replace(minute=(ts.minute // window_minutes) * window_minutes, second=0, microsecond=0)


def _ml_score(ev: Event) -> float:
    """Deterministic ML-like scoring function.

    Higher when:
    - text contains strong incident words (fake, leak, scandal, boycott, safety)
    - lower author reputation
    - higher bot_likelihood_score (where present)
    """

    text = ev.content_text.lower()
    base = 0.1
    incident_terms = ["fake", "leak", "scandal", "boycott", "safety", "deepfake"]
    for term in incident_terms:
        if term in text:
            base += 0.15
    # more suspicious if low reputation
    base += (0.5 - ev.author_reputation_score) * 0.5
    # bots add risk
    if ev.bot_likelihood_score is not None:
        base += ev.bot_likelihood_score * 0.3
    # engagement adds small risk
    base += min(ev.engagement_count, 10) * 0.01
    # clamp
    if base < 0.0:
        base = 0.0
    if base > 1.0:
        base = 1.0
    return base


def run_integrated(events: List[Event], config: DetectionConfig) -> Dict[str, float]:
    """Integrated heuristic + ML + human-review detection.

    - Per-channel volume thresholds (lower for dark_web and owned).
    - ML-like score for each event.
    - Composite risk per 15-min window.
    - If composite >= ml_thresholds.auto_alert: auto executive alert.
    - If composite >= ml_thresholds.review: route to human review; if human
      label is 'misinfo', emit human_confirmation alert.
    """

    keywords = [k.lower() for k in config.keywords]
    vt = config.per_channel_volume_thresholds
    ml_t = config.ml_thresholds

    # choose threshold per channel
    def chan_threshold(channel: str) -> int:
        if channel == "social":
            return vt.social
        if channel == "search":
            return vt.search
        if channel == "dark_web":
            return vt.dark_web
        if channel == "owned":
            return vt.owned
        return vt.social

    sorted_events = sorted(events, key=lambda e: e.timestamp)

    window_events: Dict[tuple, List[Event]] = defaultdict(list)
    window_scores: Dict[tuple, float] = defaultdict(float)
    alerts: List[IntegratedAlert] = []
    alerted_windows: Set[tuple] = set()

    total_true_misinfo_events = 0
    misinfo_events_triggered: Set[str] = set()

    # Precompute ML scores and window aggregates
    for ev in sorted_events:
        if ev.is_ground_truth_misinfo:
            total_true_misinfo_events += 1
        w_start = _window_start(ev.timestamp)
        key = (w_start, ev.channel)
        window_events[key].append(ev)
        score = _ml_score(ev)
        # composite score: average ML score of keyword-matching events or all if none
        text_l = ev.content_text.lower()
        if any(k in text_l for k in keywords):
            window_scores[key] += score
        else:
            window_scores[key] += score * 0.5

    # Heuristic + ML fusion, then human review
    for key, evs in window_events.items():
        w_start, channel = key
        th = chan_threshold(channel)
        # heuristic volume count based on keywords
        heuristic_count = 0
        keyword_events: List[Event] = []
        for ev in evs:
            text_l = ev.content_text.lower()
            if any(k in text_l for k in keywords):
                heuristic_count += 1
                keyword_events.append(ev)
        ml_sum = window_scores[key]
        count = len(evs)
        avg_ml = ml_sum / count if count > 0 else 0.0

        # composite risk combines normalized heuristic volume with avg_ml
        hv = heuristic_count / max(th, 1)
        composite = min(1.0, 0.6 * avg_ml + 0.4 * hv)

        # Auto-alert threshold
        if composite >= ml_t.auto_alert:
            if key not in alerted_windows:
                alerted_windows.add(key)
                alerts.append(
                    IntegratedAlert(
                        timestamp=w_start,
                        event_ids=[e.event_id for e in evs],
                        composite_score=composite,
                        trigger_type="fusion",
                    )
                )
            continue

        # Human-review threshold
        if composite >= ml_t.review:
            # Simulate review using human_label_decision
            any_misinfo_review = any(e.human_label_decision == "misinfo" for e in evs)
            if any_misinfo_review and key not in alerted_windows:
                alerted_windows.add(key)
                alerts.append(
                    IntegratedAlert(
                        timestamp=w_start + timedelta(minutes=config.human_review_delay_minutes),
                        event_ids=[e.event_id for e in evs if e.human_label_decision == "misinfo"],
                        composite_score=composite,
                        trigger_type="human_confirmation",
                    )
                )

    total_alerts = len(alerts)
    true_alerts = 0
    false_alerts = 0

    ev_by_id: Dict[str, Event] = {e.event_id: e for e in sorted_events}

    for alert in alerts:
        has_true = False
        for eid in alert.event_ids:
            ev = ev_by_id.get(eid)
            if ev is not None and ev.is_ground_truth_misinfo:
                has_true = True
                misinfo_events_triggered.add(ev.event_id)
        if has_true:
            true_alerts += 1
        else:
            false_alerts += 1

    detected_misinfo_events = len(misinfo_events_triggered)

    if total_alerts > 0:
        precision = true_alerts / total_alerts
    else:
        precision = 0.0

    if total_true_misinfo_events > 0:
        recall_event_level = detected_misinfo_events / total_true_misinfo_events
    else:
        recall_event_level = 0.0

    metrics: Dict[str, float] = {
        "detected_misinfo_events": float(detected_misinfo_events),
        "total_alerts": float(total_alerts),
        "true_alerts": float(true_alerts),
        "false_alerts": float(false_alerts),
        "precision": float(precision),
        "recall_event_level": float(recall_event_level),
    }
    return metrics
