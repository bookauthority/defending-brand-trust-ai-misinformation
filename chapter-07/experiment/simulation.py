import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .config import (
    AUDIENCE_SIZE,
    SEGMENTS,
    REGIONS,
    BASELINE_COEFFICIENTS,
    TREATMENT_COEFFICIENTS,
)


@dataclass
class User:
    user_id: int
    segment: str
    region: str
    baseline_trust: float
    propensity_share_misinfo: float
    sensitivity_corrections: float
    sensitivity_speed: float


@dataclass
class SocialSimulationResult:
    variant: str
    users: List[User]
    # Counts (not full logs) to keep execution light
    total_misinfo_impressions: int
    total_misinfo_shares: int
    total_corrective_impressions: int
    total_corrective_shares: int
    total_negative_sentiment_events: int
    total_events: int


def _generate_users(seed: int) -> List[User]:
    rnd = random.Random(seed)
    users: List[User] = []
    for i in range(AUDIENCE_SIZE):
        segment = rnd.choice(SEGMENTS)
        region = rnd.choice(REGIONS)
        # Baseline trust varies mildly by segment
        base_trust = {
            "employees": 0.7,
            "customers": 0.6,
            "investors": 0.55,
            "general_public": 0.5,
        }.get(segment, 0.5)
        baseline_trust = min(1.0, max(0.0, rnd.normalvariate(base_trust, 0.1)))

        propensity_share_misinfo = min(1.0, max(0.0, rnd.betavariate(2, 5)))
        sensitivity_corrections = min(1.0, max(0.0, rnd.betavariate(3, 3)))
        sensitivity_speed = min(1.0, max(0.0, rnd.betavariate(2, 4)))

        users.append(
            User(
                user_id=i,
                segment=segment,
                region=region,
                baseline_trust=baseline_trust,
                propensity_share_misinfo=propensity_share_misinfo,
                sensitivity_corrections=sensitivity_corrections,
                sensitivity_speed=sensitivity_speed,
            )
        )
    return users


def _simulate_misinformation_spread(rnd: random.Random, users: List[User]) -> Tuple[int, int, int, int]:
    """Simulate initial misinformation impressions and shares.

    Returns (impressions, shares, negative_events, total_events).
    """
    impressions = 0
    shares = 0
    negative_events = 0
    total_events = 0

    for user in users:
        # Simple model: each user has a chance to see the misinformation
        if rnd.random() < 0.7:  # 70% reach of misinfo
            impressions += 1
            total_events += 1
            # Negative sentiment more likely among lower trust users
            neg_prob = 0.4 + (0.5 * (1.0 - user.baseline_trust))
            if rnd.random() < neg_prob:
                negative_events += 1

            # User may share misinformation
            share_prob = 0.1 + 0.5 * user.propensity_share_misinfo
            if rnd.random() < share_prob:
                shares += 1
                total_events += 1
                # Sharing likely implies negativity as well
                if rnd.random() < 0.7:
                    negative_events += 1

    return impressions, shares, negative_events, total_events


def _simulate_corrective_response(
    rnd: random.Random,
    users: List[User],
    variant: str,
    misinfo_impressions: int,
    misinfo_shares: int,
    neg_events_before: int,
    total_events_before: int,
) -> Tuple[int, int, int, int]:
    """Simulate impressions/shares for corrective messages and updated sentiment.

    Returns (corrective_impressions, corrective_shares, new_negative_events, new_total_events).
    """
    if variant == "baseline":
        coeffs = BASELINE_COEFFICIENTS
    else:
        coeffs = TREATMENT_COEFFICIENTS

    corrective_impressions = 0
    corrective_shares = 0
    new_negative_events = 0
    new_total_events = 0

    # Effective base reach fraction: influenced by multiplier
    base_reach_fraction = 0.5 * coeffs.corrective_reach_multiplier
    base_reach_fraction = min(1.0, base_reach_fraction)

    for user in users:
        if rnd.random() < base_reach_fraction:
            corrective_impressions += 1
            new_total_events += 1
            # Probability user interprets corrective positively vs. negatively
            # Higher baseline trust, sensitivity to corrections, and better coeffs
            # reduce chance of negative sentiment.
            neg_prob = 0.3
            neg_prob -= 0.15 * coeffs.negative_sentiment_reduction
            neg_prob -= 0.2 * user.baseline_trust
            neg_prob -= 0.1 * user.sensitivity_corrections
            neg_prob = max(0.0, min(1.0, neg_prob))
            if rnd.random() < neg_prob:
                new_negative_events += 1

            # Sharing corrective messages: depends on trust and coeffs
            share_prob = 0.05 + 0.3 * user.baseline_trust + 0.2 * coeffs.trust_boost
            share_prob = max(0.0, min(1.0, share_prob))
            if rnd.random() < share_prob:
                corrective_shares += 1
                new_total_events += 1
                # Sharing corrective content is more likely to be neutral/positive
                if rnd.random() < 0.2:  # only small chance it's framed negatively
                    new_negative_events += 1

    return (
        corrective_impressions,
        corrective_shares,
        new_negative_events,
        new_total_events,
    )


def run_social_simulation(seed: int, variant: str) -> SocialSimulationResult:
    """Run a single social simulation for a given variant.

    The same seed yields the same underlying user population; variant controls
    corrective behavior only. This keeps baseline vs. treatment comparable.
    """
    rnd = random.Random(seed)
    users = _generate_users(seed)

    misinfo_impressions, misinfo_shares, neg_before, total_before = _simulate_misinformation_spread(
        rnd, users
    )

    (
        corrective_impressions,
        corrective_shares,
        neg_after,
        total_after,
    ) = _simulate_corrective_response(
        rnd,
        users,
        variant,
        misinfo_impressions,
        misinfo_shares,
        neg_before,
        total_before,
    )

    total_negative = neg_before + neg_after
    total_events = total_before + total_after

    return SocialSimulationResult(
        variant=variant,
        users=users,
        total_misinfo_impressions=misinfo_impressions,
        total_misinfo_shares=misinfo_shares,
        total_corrective_impressions=corrective_impressions,
        total_corrective_shares=corrective_shares,
        total_negative_sentiment_events=total_negative,
        total_events=total_events,
    )
