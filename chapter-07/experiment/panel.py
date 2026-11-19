import random
from dataclasses import dataclass
from typing import Dict, List

from .config import (
    PANEL_SIZE,
    PANEL_SEGMENTS,
    LIKERT_MIN,
    LIKERT_MAX,
    PANEL_TREATMENT_TRUST_SHIFT,
    PANEL_TREATMENT_CLARITY_SHIFT,
    PANEL_TREATMENT_WILLINGNESS_SHIFT,
    PANEL_TREATMENT_BEHAVIORAL_INTENT_DELTA,
)


@dataclass
class Panelist:
    panelist_id: int
    segment: str
    baseline_trust_in_brand: float
    risk_aversion: float
    prior_exposure: float


@dataclass
class PanelRunData:
    panelists: List[Panelist]
    # Ratings keyed by variant -> list of dicts with numeric scores
    ratings_by_variant: Dict[str, List[Dict[str, float]]]


def _clip_likert(value: float) -> float:
    return max(LIKERT_MIN, min(LIKERT_MAX, value))


def _generate_panelists(seed: int) -> List[Panelist]:
    rnd = random.Random(seed)
    panelists: List[Panelist] = []

    for i in range(PANEL_SIZE):
        segment = rnd.choice(PANEL_SEGMENTS)
        base_trust = {
            "employees": 0.7,
            "customers": 0.6,
            "investors": 0.55,
            "regulators": 0.5,
        }.get(segment, 0.5)
        baseline_trust_in_brand = min(1.0, max(0.0, rnd.normalvariate(base_trust, 0.1)))
        risk_aversion = min(1.0, max(0.0, rnd.betavariate(3, 3)))
        prior_exposure = min(1.0, max(0.0, rnd.betavariate(2, 5)))

        panelists.append(
            Panelist(
                panelist_id=i,
                segment=segment,
                baseline_trust_in_brand=baseline_trust_in_brand,
                risk_aversion=risk_aversion,
                prior_exposure=prior_exposure,
            )
        )
    return panelists


def _simulate_ratings_for_variant(
    rnd: random.Random, panelists: List[Panelist], variant: str
) -> List[Dict[str, float]]:
    ratings: List[Dict[str, float]] = []

    for p in panelists:
        base_trust_score = 3.5 + 2.0 * (p.baseline_trust_in_brand - 0.5)
        base_clarity_score = 3.5 + 1.5 * (0.5 - p.risk_aversion)
        base_willingness = 3.5 + 1.5 * (p.baseline_trust_in_brand - 0.5)

        if variant == "baseline":
            trust_score = base_trust_score + rnd.normalvariate(0.0, 0.4)
            clarity_score = base_clarity_score + rnd.normalvariate(0.0, 0.4)
            willingness = base_willingness + rnd.normalvariate(0.0, 0.4)
            behavioral_pre = 4.0 + rnd.normalvariate(0.0, 0.6)
            behavioral_post = behavioral_pre + rnd.normalvariate(0.1, 0.3)
        else:
            trust_score = (
                base_trust_score
                + PANEL_TREATMENT_TRUST_SHIFT
                + rnd.normalvariate(0.0, 0.4)
            )
            clarity_score = (
                base_clarity_score
                + PANEL_TREATMENT_CLARITY_SHIFT
                + rnd.normalvariate(0.0, 0.4)
            )
            willingness = (
                base_willingness
                + PANEL_TREATMENT_WILLINGNESS_SHIFT
                + rnd.normalvariate(0.0, 0.4)
            )
            behavioral_pre = 4.0 + rnd.normalvariate(0.0, 0.6)
            behavioral_post = (
                behavioral_pre
                + PANEL_TREATMENT_BEHAVIORAL_INTENT_DELTA
                + rnd.normalvariate(0.0, 0.3)
            )

        trust_score = _clip_likert(trust_score)
        clarity_score = _clip_likert(clarity_score)
        willingness = _clip_likert(willingness)
        behavioral_pre = _clip_likert(behavioral_pre)
        behavioral_post = _clip_likert(behavioral_post)

        ratings.append(
            {
                "trust_score": float(trust_score),
                "clarity_score": float(clarity_score),
                "willingness_to_wait_score": float(willingness),
                "behavioral_intent_pre": float(behavioral_pre),
                "behavioral_intent_post": float(behavioral_post),
            }
        )

    return ratings


def run_panel_ab_test(seed: int) -> PanelRunData:
    rnd = random.Random(seed)
    panelists = _generate_panelists(seed)

    # Same panelists evaluate both variants independently to provide
    # a controlled comparison in this offline simulation.
    ratings_baseline = _simulate_ratings_for_variant(rnd, panelists, "baseline")
    ratings_treatment = _simulate_ratings_for_variant(rnd, panelists, "treatment")

    return PanelRunData(
        panelists=panelists,
        ratings_by_variant={
            "baseline": ratings_baseline,
            "treatment": ratings_treatment,
        },
    )
