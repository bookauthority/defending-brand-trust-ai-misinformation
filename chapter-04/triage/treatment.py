from __future__ import annotations

from typing import Dict, List

from . import config


def classify_taxonomy(alert: Dict[str, object]) -> str:
    tags = set(alert.get("detected_keywords_tags", []))
    channel = str(alert.get("channel", ""))

    if {"ceo", "ceo_quote", "deepfake"} & tags:
        return "T1"
    if {"recall", "safety", "fake_recall"} & tags:
        return "T2"
    if {"earnings", "takeover", "market_rumor"} & tags or channel == "financial_forum":
        return "T3"
    if {"review", "complaint", "sentiment"} & tags:
        return "T4"
    if {"regulator", "probe", "investigation", "fine", "lawsuit"} & tags:
        return "T5"
    return "T6"


def score_impact(alert: Dict[str, object]) -> Dict[str, int]:
    reach = int(alert.get("reach_proxy", 0))
    engagement = int(alert.get("engagement_proxy", 0))
    stakeholders = alert.get("stakeholder_mentions", []) or []
    tags = alert.get("detected_keywords_tags", []) or []
    source_risk = int(alert.get("preliminary_source_risk", 0))

    reach_s = config.score_reach(reach)
    vel_s = config.score_velocity(engagement)
    audience_s = config.score_audience_criticality(stakeholders)
    cred_s = config.score_content_credibility(source_risk)
    reg_s = config.score_regulatory_trigger(tags)

    total = reach_s + vel_s + audience_s + cred_s + reg_s
    return {
        "reach": reach_s,
        "velocity": vel_s,
        "audience_criticality": audience_s,
        "content_credibility": cred_s,
        "regulatory_legal_trigger": reg_s,
        "total": total,
    }


def run_treatment(alerts: List[Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    """Run structured triage rules on alerts.

    Returns mapping from alert_id to treatment triage result.
    """

    results: Dict[str, Dict[str, object]] = {}

    for alert in alerts:
        aid = str(alert["alert_id"])
        taxonomy = classify_taxonomy(alert)
        scores = score_impact(alert)
        sev = config.severity_from_score(scores["total"])
        escalation = config.escalation_level(
            taxonomy,
            scores["total"],
            scores["audience_criticality"],
            scores["regulatory_legal_trigger"],
        )
        is_incident = escalation != "None"
        owner = config.primary_owner_for_taxonomy(taxonomy)
        requires_cf = config.needs_cross_functional(
            escalation,
            taxonomy,
            scores["regulatory_legal_trigger"],
        )

        results[aid] = {
            "variant": "treatment",
            "alert_id": aid,
            "is_incident": is_incident,
            "priority": None,
            "incident_type": taxonomy,
            "severity_level": sev,
            "escalation_level": escalation,
            "owner_team": owner,
            "requires_cross_functional_coordination": requires_cf,
        }

    return results
