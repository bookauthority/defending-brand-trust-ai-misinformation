from dataclasses import dataclass
from typing import List

CHAPTER_NUMBER = 7
EXPERIMENT_ID = "exp-ch07-comms-under-fire-ab-testing-v1"

# Single master seed for reproducible runs
DEFAULT_RANDOM_SEED = 1729


# --- Workload 1 configuration ---

AUDIENCE_SIZE = 2000  # smaller than spec for fast execution but large enough for signal
SEGMENTS: List[str] = [
    "employees",
    "customers",
    "investors",
    "general_public",
]
REGIONS: List[str] = ["NA", "EU", "APAC"]

MISINFORMATION_INITIAL_NEGATIVE_SHARE = 0.65
MISINFORMATION_INITIAL_NEUTRAL_SHARE = 0.25
MISINFORMATION_INITIAL_POSITIVE_SHARE = 0.10

# Time is modeled in arbitrary units; we do not simulate explicit timestamps for each event,
# but we track counts pre- and post-response and compare cohorts.


@dataclass
class ResponseBehaviorCoefficients:
    """Coefficients controlling how messages affect user behavior.

    This is a simple parametric model designed only for relative comparisons.
    """

    trust_boost: float
    clarity_boost: float
    misinformation_share_reduction: float
    negative_sentiment_reduction: float
    corrective_reach_multiplier: float


# Baseline: modest impact
BASELINE_COEFFICIENTS = ResponseBehaviorCoefficients(
    trust_boost=0.2,
    clarity_boost=0.1,
    misinformation_share_reduction=0.10,
    negative_sentiment_reduction=0.10,
    corrective_reach_multiplier=1.0,
)

# Treatment: stronger, psychology-informed impact
TREATMENT_COEFFICIENTS = ResponseBehaviorCoefficients(
    trust_boost=0.6,
    clarity_boost=0.5,
    misinformation_share_reduction=0.25,
    negative_sentiment_reduction=0.30,
    corrective_reach_multiplier=1.3,
)


# --- Workload 2 configuration ---

PANEL_SIZE = 800  # per run (shared across variants)
PANEL_SEGMENTS: List[str] = [
    "employees",
    "customers",
    "investors",
    "regulators",
]

# Likert scale min/max for panel scores
LIKERT_MIN = 1.0
LIKERT_MAX = 7.0

# Mean shift parameters for treatment relative to baseline
PANEL_TREATMENT_TRUST_SHIFT = 0.7
PANEL_TREATMENT_CLARITY_SHIFT = 0.6
PANEL_TREATMENT_WILLINGNESS_SHIFT = 0.5
PANEL_TREATMENT_BEHAVIORAL_INTENT_DELTA = -0.4


# --- Workload 3 configuration ---

# A simple factor translating improved negative sentiment into a faster
# stabilization time (in arbitrary units). This is not bound to real hours.
BASELINE_STABILIZATION_BASE = 10.0
TREATMENT_STABILIZATION_BASE = 8.0

__all__ = [
    "CHAPTER_NUMBER",
    "EXPERIMENT_ID",
    "DEFAULT_RANDOM_SEED",
    "AUDIENCE_SIZE",
    "SEGMENTS",
    "REGIONS",
    "MISINFORMATION_INITIAL_NEGATIVE_SHARE",
    "MISINFORMATION_INITIAL_NEUTRAL_SHARE",
    "MISINFORMATION_INITIAL_POSITIVE_SHARE",
    "ResponseBehaviorCoefficients",
    "BASELINE_COEFFICIENTS",
    "TREATMENT_COEFFICIENTS",
    "PANEL_SIZE",
    "PANEL_SEGMENTS",
    "LIKERT_MIN",
    "LIKERT_MAX",
    "PANEL_TREATMENT_TRUST_SHIFT",
    "PANEL_TREATMENT_CLARITY_SHIFT",
    "PANEL_TREATMENT_WILLINGNESS_SHIFT",
    "PANEL_TREATMENT_BEHAVIORAL_INTENT_DELTA",
    "BASELINE_STABILIZATION_BASE",
    "TREATMENT_STABILIZATION_BASE",
]
