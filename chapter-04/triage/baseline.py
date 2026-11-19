from __future__ import annotations

import random
from typing import Dict, List


def run_baseline(alerts: List[Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    """Simulate unstructured analyst triage.

    This is intentionally heuristic and slightly noisy to approximate
    inconsistency, but uses a fixed RNG seed for reproducibility.

    Returns a mapping from alert_id to baseline triage result.
    """

    rng = random.Random(424242)
    results: Dict[str, Dict[str, object]] = {}

    for alert in alerts:
        aid = str(alert["alert_id"])
        reach = int(alert.get("reach_proxy", 0))
        engagement = int(alert.get("engagement_proxy", 0))
        tags = set(alert.get("detected_keywords_tags", []))

        risk_score = 0
        if reach > 10000:
            risk_score += 1
        if engagement > 1000:
            risk_score += 1
        if {"recall", "deepfake", "ceo", "regulator", "earnings"} & tags:
            risk_score += 2

        # Random noise to simulate analyst subjectivity
        noise = rng.choice([-1, 0, 0, 1])
        risk_score += noise
        if risk_score < 0:
            risk_score = 0

        is_incident = risk_score >= 2

        if risk_score <= 1:
            priority = "Low"
        elif risk_score == 2:
            priority = "Medium"
        else:
            priority = "High"

        # Very rough owner guess
        if {"ceo", "deepfake", "ceo_quote"} & tags:
            owner = "Comms/Brand"
        elif {"recall", "safety"} & tags:
            owner = "Product/Operations"
        elif {"earnings", "takeover"} & tags:
            owner = "Legal"
        elif {"regulator", "probe", "investigation"} & tags:
            owner = "Legal"
        else:
            owner = "Comms/Brand"

        # Baseline does not use structured severity; approximate
        if priority == "Low":
            severity = "S1"
        elif priority == "Medium":
            severity = "S2"
        else:
            severity = "S3"

        # Escalation flag loosely tied to severity
        if severity == "S3" and risk_score >= 4:
            escalation = "S3"
        elif severity == "S3":
            escalation = "S2"
        elif severity == "S2":
            escalation = "S1"
        else:
            escalation = "None"

        # Assume no explicit cross-functional coordination in baseline
        requires_cf = False

        results[aid] = {
            "variant": "baseline",
            "alert_id": aid,
            "is_incident": is_incident,
            "priority": priority,
            "incident_type": None,  # no taxonomy
            "severity_level": severity,
            "escalation_level": escalation,
            "owner_team": owner,
            "requires_cross_functional_coordination": requires_cf,
        }

    return results
