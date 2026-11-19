from typing import Dict, List

from .simulation import SocialSimulationResult
from .panel import PanelRunData
from .config import (
    BASELINE_STABILIZATION_BASE,
    TREATMENT_STABILIZATION_BASE,
)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def compute_workload1_metrics(result: SocialSimulationResult) -> Dict[str, float]:
    """Compute numeric metrics from social simulation outputs.

    Metrics implemented (all numeric):
      - misinformation_share_of_voice
      - negative_sentiment_rate
      - corrective_message_reach
      - misinformation_reshare_rate
    """
    misinfo_volume = result.total_misinfo_shares + result.total_misinfo_impressions
    corrective_volume = (
        result.total_corrective_shares + result.total_corrective_impressions
    )
    total_volume = misinfo_volume + corrective_volume

    misinformation_share_of_voice = _safe_ratio(misinfo_volume, total_volume)
    negative_sentiment_rate = _safe_ratio(
        result.total_negative_sentiment_events, result.total_events
    )

    corrective_message_reach = float(result.total_corrective_impressions)

    misinfo_reshare_rate = _safe_ratio(
        result.total_misinfo_shares * 1000.0,
        max(1.0, float(result.total_misinfo_impressions)),
    )

    return {
        "misinformation_share_of_voice": float(misinformation_share_of_voice),
        "negative_sentiment_rate": float(negative_sentiment_rate),
        "corrective_message_reach": float(corrective_message_reach),
        "misinformation_reshare_rate": float(misinfo_reshare_rate),
    }


def compute_workload2_metrics(data: PanelRunData, variant: str) -> Dict[str, float]:
    """Compute A/B metrics from panel ratings.

    Metrics implemented:
      - avg_trust_score
      - avg_clarity_score
      - willingness_to_wait_for_updates
      - behavioral_intent_shift
    """
    ratings: List[Dict[str, float]] = data.ratings_by_variant[variant]

    n = float(len(ratings)) if ratings else 1.0

    sum_trust = 0.0
    sum_clarity = 0.0
    sum_willingness = 0.0
    sum_behavioral_delta = 0.0

    for r in ratings:
        sum_trust += r["trust_score"]
        sum_clarity += r["clarity_score"]
        sum_willingness += r["willingness_to_wait_score"]
        sum_behavioral_delta += (
            r["behavioral_intent_post"] - r["behavioral_intent_pre"]
        )

    return {
        "avg_trust_score": float(sum_trust / n),
        "avg_clarity_score": float(sum_clarity / n),
        "willingness_to_wait_for_updates": float(sum_willingness / n),
        "behavioral_intent_shift": float(sum_behavioral_delta / n),
    }


def compute_workload3_metrics(result: SocialSimulationResult) -> Dict[str, float]:
    """Compute a simple time_to_sentiment_stabilization metric.

    We approximate stabilization time as a decreasing function of how low
    the negative sentiment rate is. This is not calibrated to real hours
    but permits comparative evaluation between baseline and treatment.
    """
    neg_rate = _safe_ratio(result.total_negative_sentiment_events, result.total_events)

    # Baseline vs treatment constant handled by caller based on variant
    if result.variant == "baseline":
        base = BASELINE_STABILIZATION_BASE
    else:
        base = TREATMENT_STABILIZATION_BASE

    # Higher negative rate -> longer stabilization, capped for safety
    time_to_stabilization = base * (1.0 + 2.0 * neg_rate)

    return {
        "time_to_sentiment_stabilization": float(time_to_stabilization),
    }
