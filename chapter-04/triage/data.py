from __future__ import annotations

import random
from typing import Dict, List, Tuple


Alert = Dict[str, object]
Truth = Dict[str, Dict[str, object]]


def _base_alert(alert_id: str, timestamp: str, channel: str) -> Alert:
    return {
        "alert_id": alert_id,
        "timestamp": timestamp,
        "channel": channel,
        "suspected_content_type": "text",
        "preliminary_source_risk": 1,
        "detected_keywords_tags": [],
        "reach_proxy": 0,
        "engagement_proxy": 0,
        "stakeholder_mentions": [],
        "geo_or_market": "global",
        "pre_flagged_category": None,
    }


def generate_low_mid_risk_alerts() -> Tuple[List[Alert], Truth]:
    """Generate a deterministic low-to-mid risk alert stream and ground truth.

    Returns (alerts, truth_mapping).
    """

    rng = random.Random(12345)
    alerts: List[Alert] = []
    truth: Truth = {}

    # Small synthetic review campaign (T4, S1)
    for i in range(10):
        aid = f"LM-T4-{i}"
        alert = _base_alert(aid, f"2026-01-01T0{i:02d}:00Z", "twitter")
        alert["reach_proxy"] = 500 + i * 50
        alert["engagement_proxy"] = 5 + i
        alert["detected_keywords_tags"] = ["review", "complaint"]
        alert["stakeholder_mentions"] = ["customers"]
        alerts.append(alert)
        truth[aid] = {
            "incident_type": "T4",
            "severity_level": "S1",
            "escalation_level": "S1",
            "owner_team": "Comms/Brand",
            "is_true_incident": True,
            "is_true_high_severity": False,
        }

    # Minor product quality rumor (T2, S2)
    for i in range(5):
        aid = f"LM-T2-{i}"
        alert = _base_alert(aid, f"2026-01-01T1{i:02d}:00Z", "news_blog")
        alert["reach_proxy"] = 5000 + i * 1000
        alert["engagement_proxy"] = 50 + i * 10
        alert["detected_keywords_tags"] = ["rumor", "quality"]
        alert["stakeholder_mentions"] = ["customers"]
        alerts.append(alert)
        truth[aid] = {
            "incident_type": "T2",
            "severity_level": "S2",
            "escalation_level": "S2",
            "owner_team": "Comms/Brand",
            "is_true_incident": True,
            "is_true_high_severity": False,
        }

    # Benign noise (non-incident, T6)
    for i in range(5):
        aid = f"LM-NOISE-{i}"
        alert = _base_alert(aid, f"2026-01-01T2{i:02d}:00Z", "twitter")
        alert["reach_proxy"] = 100
        alert["engagement_proxy"] = 1
        alerts.append(alert)
        truth[aid] = {
            "incident_type": "T6",
            "severity_level": "S1",
            "escalation_level": "None",
            "owner_team": "Comms/Brand",
            "is_true_incident": False,
            "is_true_high_severity": False,
        }

    # Early-stage fake executive quote (T1, S3 but moderate scale)
    for i in range(3):
        aid = f"LM-T1-{i}"
        alert = _base_alert(aid, f"2026-01-01T3{i:02d}:00Z", "twitter")
        alert["reach_proxy"] = 20000 + i * 5000
        alert["engagement_proxy"] = 200 + i * 50
        alert["detected_keywords_tags"] = ["ceo_quote", "rumor"]
        alert["stakeholder_mentions"] = ["investors", "employees"]
        alert["preliminary_source_risk"] = 2
        alerts.append(alert)
        truth[aid] = {
            "incident_type": "T1",
            "severity_level": "S3",
            "escalation_level": "S3",
            "owner_team": "Comms/Brand",
            "is_true_incident": True,
            "is_true_high_severity": True,
        }

    return alerts, truth


def generate_high_mixed_alerts() -> Tuple[List[Alert], Truth]:
    """Generate a deterministic high-risk-and-mixed alert stream and ground truth."""

    rng = random.Random(67890)
    alerts: List[Alert] = []
    truth: Truth = {}

    # Viral deepfake CEO video (T1, S4)
    for i in range(5):
        aid = f"HM-T1-DF-{i}"
        alert = _base_alert(aid, f"2026-01-02T0{i:02d}:00Z", "tiktok")
        alert["suspected_content_type"] = "video"
        alert["reach_proxy"] = 200000 + i * 50000
        alert["engagement_proxy"] = 5000 + i * 1000
        alert["detected_keywords_tags"] = ["ceo", "deepfake", "market_rumor"]
        alert["stakeholder_mentions"] = ["investors", "employees", "key_customers"]
        alert["preliminary_source_risk"] = 3
        alerts.append(alert)
        truth[aid] = {
            "incident_type": "T1",
            "severity_level": "S4",
            "escalation_level": "S4",
            "owner_team": "Comms/Brand",
            "is_true_incident": True,
            "is_true_high_severity": True,
        }

    # Fabricated product recall (T2, S4)
    for i in range(4):
        aid = f"HM-T2-RECALL-{i}"
        alert = _base_alert(aid, f"2026-01-02T1{i:02d}:00Z", "twitter")
        alert["reach_proxy"] = 100000 + i * 20000
        alert["engagement_proxy"] = 3000 + i * 500
        alert["detected_keywords_tags"] = ["recall", "safety", "probe"]
        alert["stakeholder_mentions"] = ["customers", "regulators"]
        alert["preliminary_source_risk"] = 3
        alerts.append(alert)
        truth[aid] = {
            "incident_type": "T2",
            "severity_level": "S4",
            "escalation_level": "S4",
            "owner_team": "Comms/Brand",
            "is_true_incident": True,
            "is_true_high_severity": True,
        }

    # Market manipulation rumor (T3, S3)
    for i in range(3):
        aid = f"HM-T3-MARKET-{i}"
        alert = _base_alert(aid, f"2026-01-02T2{i:02d}:00Z", "financial_forum")
        alert["reach_proxy"] = 50000 + i * 10000
        alert["engagement_proxy"] = 2000 + i * 200
        alert["detected_keywords_tags"] = ["earnings", "takeover", "rumor"]
        alert["stakeholder_mentions"] = ["investors"]
        alert["preliminary_source_risk"] = 2
        alerts.append(alert)
        truth[aid] = {
            "incident_type": "T3",
            "severity_level": "S3",
            "escalation_level": "S3",
            "owner_team": "Legal",
            "is_true_incident": True,
            "is_true_high_severity": True,
        }

    # Fake regulatory probe leak (T5, S3)
    for i in range(2):
        aid = f"HM-T5-REG-{i}"
        alert = _base_alert(aid, f"2026-01-02T3{i:02d}:00Z", "news_blog")
        alert["reach_proxy"] = 60000 + i * 5000
        alert["engagement_proxy"] = 1500 + i * 200
        alert["detected_keywords_tags"] = ["regulator", "probe", "investigation"]
        alert["stakeholder_mentions"] = ["regulators", "investors"]
        alert["preliminary_source_risk"] = 2
        alerts.append(alert)
        truth[aid] = {
            "incident_type": "T5",
            "severity_level": "S3",
            "escalation_level": "S3",
            "owner_team": "Legal",
            "is_true_incident": True,
            "is_true_high_severity": True,
        }

    # Benign noise again
    for i in range(5):
        aid = f"HM-NOISE-{i}"
        alert = _base_alert(aid, f"2026-01-02T4{i:02d}:00Z", "twitter")
        alert["reach_proxy"] = 50
        alert["engagement_proxy"] = 1
        alerts.append(alert)
        truth[aid] = {
            "incident_type": "T6",
            "severity_level": "S1",
            "escalation_level": "None",
            "owner_team": "Comms/Brand",
            "is_true_incident": False,
            "is_true_high_severity": False,
        }

    return alerts, truth
