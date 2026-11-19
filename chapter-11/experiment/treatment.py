import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .config import default_experiment_config, choose_team_for_alert
from .metrics import aggregate_metrics
from .utils import SyntheticAlert, gen_id


@dataclass
class TreatmentEvent:
    alert_id: str
    timestamp_detected: datetime
    timestamp_received: datetime
    timestamp_routed_chat: datetime
    timestamp_routed_ticket: datetime
    severity: int


def generate_alerts_treatment(
    alert_count: int,
    duration_minutes: int,
    seed: int,
    profile: str,
) -> List[SyntheticAlert]:
    # Keep identical generation as baseline by delegating
    from .baseline import generate_alerts

    return generate_alerts(alert_count, duration_minutes, seed, profile)


def simulate_treatment_flow(
    alerts: List[SyntheticAlert], profile: str, seed: int
) -> List[TreatmentEvent]:
    rng = random.Random(seed + 12345)
    config = default_experiment_config()
    events: List[TreatmentEvent] = []

    for alert in alerts:
        # webhook receipt almost immediately after detection
        receipt_delay_sec = rng.uniform(1, 10)  # seconds
        timestamp_received = alert.timestamp_detected + timedelta(seconds=receipt_delay_sec)

        # routing/processing times
        if profile == "failure":
            chat_processing_sec = rng.uniform(5, 30)
            ticket_processing_sec = rng.uniform(10, 40)
        else:
            chat_processing_sec = rng.uniform(1, 5)
            ticket_processing_sec = rng.uniform(2, 10)

        timestamp_chat = timestamp_received + timedelta(seconds=chat_processing_sec)
        timestamp_ticket = timestamp_received + timedelta(seconds=ticket_processing_sec)

        team = choose_team_for_alert(alert.source_channel, alert.severity_score, config)
        if team is None:
            # Not routed anywhere; skip event creation
            continue

        events.append(
            TreatmentEvent(
                alert_id=alert.alert_id,
                timestamp_detected=alert.timestamp_detected,
                timestamp_received=timestamp_received,
                timestamp_routed_chat=timestamp_chat,
                timestamp_routed_ticket=timestamp_ticket,
                severity=alert.severity_score,
            )
        )

    return events


def run_treatment_workload(
    workload_id: str,
    alert_count: int,
    duration_minutes: int,
    seed: int,
    profile: str,
) -> Dict[str, Any]:
    alerts = generate_alerts_treatment(alert_count, duration_minutes, seed, profile)
    events = simulate_treatment_flow(alerts, profile, seed)

    eligible_alert_ids = [a.alert_id for a in alerts if a.severity_score >= 3]

    alert_to_ticket_latencies: List[float] = []
    alert_to_chat_latencies: List[float] = []
    routed_alert_ids: List[str] = []

    for ev in events:
        if ev.severity >= 3:
            det = ev.timestamp_detected
            ticket_latency = (ev.timestamp_routed_ticket - det).total_seconds()
            chat_latency = (ev.timestamp_routed_chat - det).total_seconds()
            alert_to_ticket_latencies.append(ticket_latency)
            alert_to_chat_latencies.append(chat_latency)
            routed_alert_ids.append(ev.alert_id)

    metrics = aggregate_metrics(
        alert_to_ticket_latencies,
        alert_to_chat_latencies,
        routed_alert_ids,
        eligible_alert_ids,
    )

    metrics = {
        k: (0.0 if (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else float(v))
        for k, v in metrics.items()
    }

    run_id = f"treatment_{workload_id}"
    return {
        "run_id": run_id,
        "success": True,
        "metrics": metrics,
    }
