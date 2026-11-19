from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Set

from .config_loader import DetectionConfig
from .workloads import Event


@dataclass
class Alert:
    timestamp: datetime
    event_ids: List[str]


def _window_start(ts: datetime, window_minutes: int = 15) -> datetime:
    return ts.replace(minute=(ts.minute // window_minutes) * window_minutes, second=0, microsecond=0)


def run_baseline(events: List[Event], config: DetectionConfig) -> Dict[str, float]:
    """Heuristics-only detection.

    - Keyword match against configured list
    - Volume spike detection: if count of matching events per 15-min window per channel
      exceeds baseline_volume_threshold, raise an alert.
    - Channel-agnostic thresholds (single threshold in config).
    """

    keywords = [k.lower() for k in config.keywords]
    threshold = config.baseline_volume_threshold

    # sort events by time
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    window_counts: Dict[tuple, int] = defaultdict(int)
    window_events: Dict[tuple, List[Event]] = defaultdict(list)
    alerts: List[Alert] = []
    alerted_windows: Set[tuple] = set()

    total_true_misinfo_events = 0
    misinfo_events_triggered: Set[str] = set()

    for ev in sorted_events:
        if ev.is_ground_truth_misinfo:
            total_true_misinfo_events += 1
        text_l = ev.content_text.lower()
        if any(k in text_l for k in keywords):
            w_start = _window_start(ev.timestamp)
            key = (w_start, ev.channel)
            window_counts[key] += 1
            window_events[key].append(ev)
            if window_counts[key] >= threshold and key not in alerted_windows:
                alerted_windows.add(key)
                alert_event_ids = [e.event_id for e in window_events[key]]
                alerts.append(Alert(timestamp=w_start, event_ids=alert_event_ids))

    total_alerts = len(alerts)
    true_alerts = 0
    false_alerts = 0

    for alert in alerts:
        # An alert is "true" if any included event is misinfo
        ev_ids_set = set(alert.event_ids)
        has_true = False
        for ev in sorted_events:
            if ev.event_id in ev_ids_set and ev.is_ground_truth_misinfo:
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
