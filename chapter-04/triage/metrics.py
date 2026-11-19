from __future__ import annotations

from typing import Dict, Iterable


def _collect_incidents(
    results: Dict[str, Dict[str, object]],
    truth: Dict[str, Dict[str, object]],
):
    """Helper to iterate over (alert_id, predicted, actual) for true incidents.

    True incidents are those where truth[aid]["is_true_incident"] is True.
    """

    for aid, gt in truth.items():
        pred = results.get(aid)
        if pred is None:
            continue
        if not gt.get("is_true_incident", False):
            continue
        yield aid, pred, gt


def alert_to_incident_conversion_rate(
    results: Dict[str, Dict[str, object]],
    truth: Dict[str, Dict[str, object]],
) -> float:
    total_alerts = len(truth)
    if total_alerts == 0:
        return 0.0
    incident_count = sum(
        1 for r in results.values() if bool(r.get("is_incident", False))
    )
    return (incident_count / total_alerts) * 100.0


def high_severity_incident_detection_rate(
    results: Dict[str, Dict[str, object]],
    truth: Dict[str, Dict[str, object]],
) -> float:
    true_high = [
        (aid, gt)
        for aid, gt in truth.items()
        if gt.get("is_true_incident") and gt.get("is_true_high_severity")
    ]
    if not true_high:
        return 0.0
    detected = 0
    for aid, gt in true_high:
        pred = results.get(aid)
        if pred is None:
            continue
        pred_sev = str(pred.get("severity_level", ""))
        if pred_sev in {"S3", "S4"}:
            detected += 1
    return (detected / len(true_high)) * 100.0


def misrouted_incident_rate(
    results: Dict[str, Dict[str, object]],
    truth: Dict[str, Dict[str, object]],
) -> float:
    incidents = list(_collect_incidents(results, truth))
    if not incidents:
        return 0.0
    misrouted = 0
    for _, pred, gt in incidents:
        if str(pred.get("owner_team")) != str(gt.get("owner_team")):
            misrouted += 1
    return (misrouted / len(incidents)) * 100.0


def severity_misclassification_rate(
    results: Dict[str, Dict[str, object]],
    truth: Dict[str, Dict[str, object]],
) -> float:
    incidents = list(_collect_incidents(results, truth))
    if not incidents:
        return 0.0
    mis = 0
    for _, pred, gt in incidents:
        if str(pred.get("severity_level")) != str(gt.get("severity_level")):
            mis += 1
    return (mis / len(incidents)) * 100.0


def cross_functional_escalation_accuracy(
    results: Dict[str, Dict[str, object]],
    truth: Dict[str, Dict[str, object]],
) -> float:
    # Compare for true S3-S4 ground truth incidents
    high_truth = [
        (aid, gt)
        for aid, gt in truth.items()
        if gt.get("is_true_incident") and gt.get("severity_level") in {"S3", "S4"}
    ]
    if not high_truth:
        return 0.0
    correct = 0
    for aid, gt in high_truth:
        pred = results.get(aid)
        if pred is None:
            continue
        # For this simulation, we treat requires_cross_functional_coordination
        # True as "escalated to all required functions".
        if bool(pred.get("requires_cross_functional_coordination", False)):
            correct += 1
    return (correct / len(high_truth)) * 100.0


def compute_all_metrics(
    results: Dict[str, Dict[str, object]],
    truth: Dict[str, Dict[str, object]],
) -> Dict[str, float]:
    """Compute all numeric metrics required for the evidence file.

    Metrics that cannot be measured in this sandbox (e.g., real time-based
    measures) are intentionally omitted.
    """

    return {
        "alert_to_incident_conversion_rate": alert_to_incident_conversion_rate(
            results, truth
        ),
        "high_severity_incident_detection_rate": high_severity_incident_detection_rate(
            results, truth
        ),
        "misrouted_incident_rate": misrouted_incident_rate(results, truth),
        "severity_misclassification_rate": severity_misclassification_rate(
            results, truth
        ),
        # median_time_to_classification intentionally omitted (no timing here)
        # alert_fatigue_proxy_rate and incident_consistency_score are also
        # omitted, as they require human or multi-run behaviour.
        "cross_functional_escalation_accuracy": cross_functional_escalation_accuracy(
            results, truth
        ),
    }
