from dataclasses import dataclass
from typing import Dict, List, Tuple


# Taxonomy labels (T1–T6)
TAXONOMY = {
    "T1": "Executive/Leadership Persona Attack",
    "T2": "Product/Service Harm or Safety Narrative",
    "T3": "Market/Financial Manipulation Narrative",
    "T4": "Customer/Employee Sentiment Manipulation",
    "T5": "Institutional Legitimacy Narrative",
    "T6": "Other/Unknown",
}


SEVERITY_THRESHOLDS = {
    "S1": (0, 3),   # inclusive lower, inclusive upper
    "S2": (4, 6),
    "S3": (7, 9),
    "S4": (10, 15),
}


@dataclass(frozen=True)
class OwnershipMapping:
    primary_owner: str
    consulted: Tuple[str, ...]


# Simplified ownership model keyed by (taxonomy, severity)
# For this experiment we use broad rules to keep logic readable.
OWNERSHIP_RULES: Dict[str, OwnershipMapping] = {
    "T1": OwnershipMapping("Comms/Brand", ("Legal",)),
    "T2": OwnershipMapping("Comms/Brand", ("Product/Operations", "Security/Risk")),
    "T3": OwnershipMapping("Legal", ("Security/Risk",)),
    "T4": OwnershipMapping("Comms/Brand", tuple()),
    "T5": OwnershipMapping("Legal", ("Security/Risk",)),
    "T6": OwnershipMapping("Comms/Brand", tuple()),
}


# Dimensions used to derive impact scores
IMPACT_DIMENSIONS: List[str] = [
    "reach",
    "velocity",
    "audience_criticality",
    "content_credibility",
    "regulatory_legal_trigger",
]


def score_reach(reach_proxy: int) -> int:
    if reach_proxy <= 1000:
        return 0
    if reach_proxy <= 10000:
        return 1
    if reach_proxy <= 100000:
        return 2
    return 3


def score_velocity(engagement_proxy: int) -> int:
    if engagement_proxy <= 10:
        return 0
    if engagement_proxy <= 100:
        return 1
    if engagement_proxy <= 1000:
        return 2
    return 3


def score_audience_criticality(stakeholder_mentions) -> int:
    if not stakeholder_mentions:
        return 0
    critical = {"regulators", "investors", "key_customers", "employees"}
    mentions = set(stakeholder_mentions)
    overlap = mentions & critical
    if not overlap:
        return 1
    if len(overlap) == 1:
        return 2
    return 3


def score_content_credibility(preliminary_source_risk: int) -> int:
    # Use source risk as a proxy for credibility (higher is worse)
    if preliminary_source_risk <= 0:
        return 0
    if preliminary_source_risk == 1:
        return 1
    if preliminary_source_risk == 2:
        return 2
    return 3


def score_regulatory_trigger(tags) -> int:
    if not tags:
        return 0
    tags = set(tags)
    if {"regulator", "sec", "fine", "lawsuit"} & tags:
        return 3
    if {"recall", "probe", "investigation"} & tags:
        return 2
    if {"complaint", "rumor"} & tags:
        return 1
    return 0


def severity_from_score(total_score: int) -> str:
    for sev, (low, high) in SEVERITY_THRESHOLDS.items():
        if low <= total_score <= high:
            return sev
    # Clamp out-of-range just in case
    if total_score < 0:
        return "S1"
    return "S4"


def escalation_level(taxonomy: str, total_score: int, audience_score: int, reg_score: int) -> str:
    # ALERT_ONLY when very low impact and not T1–T3
    if total_score <= 2 and taxonomy not in {"T1", "T2", "T3"}:
        return "None"

    # Determine base severity
    sev = severity_from_score(total_score)

    if total_score >= 10 or reg_score >= 3:
        return "S4"
    if total_score >= 7 or audience_score == 3 or reg_score >= 2:
        return "S3"
    if total_score >= 3 or taxonomy in {"T1", "T2", "T3", "T4", "T5"}:
        # S1 or S2 incident
        return sev
    return "None"


def needs_cross_functional(escalation: str, taxonomy: str, reg_score: int) -> bool:
    if escalation in {"S3", "S4"}:
        return True
    if taxonomy in {"T2", "T3", "T5"} and reg_score >= 2:
        return True
    return False


def primary_owner_for_taxonomy(taxonomy: str) -> str:
    mapping = OWNERSHIP_RULES.get(taxonomy)
    if mapping is None:
        return "Comms/Brand"
    return mapping.primary_owner
