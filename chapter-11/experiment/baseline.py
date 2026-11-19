import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .metrics import aggregate_metrics
from .utils import SyntheticAlert, gen_id


@dataclass
class BaselineEvent:
    alert_id: str
    timestamp_detected: datetime
    timestamp_exported: datetime
    timestamp_triaged: datetime
    timestamp_chat_posted: datetime
    timestamp_ticket_created: datetime
    severity: int


def generate_alerts(
    alert_count: int,
    duration_minutes: int,
    seed: int,
    profile: str,
) -> List[SyntheticAlert]:
    rng = random.Random(seed)
    start = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    alerts: List[SyntheticAlert] = []

    channels_steady = ["twitter", "tiktok", "news"]
    channels_spike = ["twitter", "tiktok", "youtube", "internal_tipline"]

    for i in range(alert_count):
        if profile == "steady":
            offset_min = rng.uniform(0, duration_minutes)
            channel = rng.choice(channels_steady)
        elif profile == "spike":
            # concentrate near the end
            offset_min = rng.uniform(duration_minutes * 0.5, duration_minutes)
            channel = rng.choice(channels_spike)
        elif profile == "failure":
            offset_min = rng.uniform(0, duration_minutes)
            channel = rng.choice(channels_steady)
        else:
            offset_min = rng.uniform(0, duration_minutes)
            channel = rng.choice(channels_steady)

        severity = rng.choices([1, 2, 3, 4, 5], weights=[3, 3, 2.5, 1, 0.5])[0]
        alert_id = gen_id("alert", rng)
        ts = start + timedelta(minutes=offset_min)
        alerts.append(SyntheticAlert(alert_id=alert_id, timestamp_detected=ts, severity_score=severity, source_channel=channel))

    # Sort by detection time for realism
    alerts.sort(key=lambda a: a.timestamp_detected)
    return alerts


def simulate_baseline_flow(
    alerts: List[SyntheticAlert], duration_minutes: int, profile: str, seed: int
) -> List[BaselineEvent]:
    rng = random.Random(seed + 9999)
    # manual export every 10 minutes
    export_interval = 10.0
    events: List[BaselineEvent] = []

    if not alerts:
        return events

    start = alerts[0].timestamp_detected

    # group alerts into export batches
    batches: Dict[int, List[SyntheticAlert]] = {}
    for alert in alerts:
        minutes_since_start = (alert.timestamp_detected - start).total_seconds() / 60.0
        batch_index = int(minutes_since_start // export_interval)
        batches.setdefault(batch_index, []).append(alert)

    for batch_index, batch_alerts in batches.items():
        export_time = start + timedelta(minutes=(batch_index + 1) * export_interval)
        for alert in batch_alerts:
            # triage happens some minutes after export
            if profile == "spike":
                triage_delay_min = rng.uniform(5, 20)
            else:
                triage_delay_min = rng.uniform(2, 15)
            triage_time = export_time + timedelta(minutes=triage_delay_min)

            # manual chat post delay
            if profile == "spike":
                chat_delay_min = rng.uniform(2, 10)
            else:
                chat_delay_min = rng.uniform(1, 5)
            chat_time = triage_time + timedelta(minutes=chat_delay_min)

            # manual ticket creation delay
            if profile == "spike":
                ticket_delay_min = rng.uniform(5, 15)
            else:
                ticket_delay_min = rng.uniform(2, 8)
            ticket_time = chat_time + timedelta(minutes=ticket_delay_min)

            events.append(
                BaselineEvent(
                    alert_id=alert.alert_id,
                    timestamp_detected=alert.timestamp_detected,
                    timestamp_exported=export_time,
                    timestamp_triaged=triage_time,
                    timestamp_chat_posted=chat_time,
                    timestamp_ticket_created=ticket_time,
                    severity=alert.severity_score,
                )
            )

    return events


def run_baseline_workload(
    workload_id: str,
    alert_count: int,
    duration_minutes: int,
    seed: int,
    profile: str,
) -> Dict[str, Any]:
    alerts = generate_alerts(alert_count, duration_minutes, seed, profile)
    events = simulate_baseline_flow(alerts, duration_minutes, profile, seed)

    # Routing criteria: severity >= 3 should lead to both chat and ticket
    eligible_alert_ids = [a.alert_id for a in alerts if a.severity_score >= 3]

    alert_to_ticket_latencies: List[float] = []
    alert_to_chat_latencies: List[float] = []
    routed_alert_ids: List[str] = []

    for ev in events:
        if ev.severity >= 3:
            det = ev.timestamp_detected
            ticket_latency = (ev.timestamp_ticket_created - det).total_seconds()
            chat_latency = (ev.timestamp_chat_posted - det).total_seconds()
            alert_to_ticket_latencies.append(ticket_latency)
            alert_to_chat_latencies.append(chat_latency)
            routed_alert_ids.append(ev.alert_id)

    metrics = aggregate_metrics(
        alert_to_ticket_latencies,
        alert_to_chat_latencies,
        routed_alert_ids,
        eligible_alert_ids,
    )

    # Ensure all metric values are finite numbers
    metrics = {
        k: (0.0 if (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else float(v))
        for k, v in metrics.items()
    }

    run_id = f"baseline_{workload_id}"
    return {
        "run_id": run_id,
        "success": True,
        "metrics": metrics,
    }
