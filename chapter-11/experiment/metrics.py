from typing import Dict, List, Tuple

from .utils import median


def compute_latency_metrics(
    alert_to_ticket_latencies: List[float], alert_to_chat_latencies: List[float]
) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    if alert_to_ticket_latencies:
        metrics["end_to_end_alert_to_ticket_latency_median_sec"] = float(
            median(alert_to_ticket_latencies)
        )
    if alert_to_chat_latencies:
        metrics["end_to_end_alert_to_chat_latency_median_sec"] = float(
            median(alert_to_chat_latencies)
        )
    return metrics


def compute_routing_coverage(
    routed_alert_ids: List[str], eligible_alert_ids: List[str]
) -> float:
    if not eligible_alert_ids:
        return 0.0
    eligible_set = set(eligible_alert_ids)
    routed_set = set(routed_alert_ids)
    covered = len(eligible_set & routed_set)
    return float(covered / len(eligible_set))


def aggregate_metrics(
    alert_to_ticket_latencies: List[float],
    alert_to_chat_latencies: List[float],
    routed_alert_ids: List[str],
    eligible_alert_ids: List[str],
) -> Dict[str, float]:
    metrics = compute_latency_metrics(alert_to_ticket_latencies, alert_to_chat_latencies)
    metrics["alert_routing_coverage"] = compute_routing_coverage(
        routed_alert_ids, eligible_alert_ids
    )
    return metrics
