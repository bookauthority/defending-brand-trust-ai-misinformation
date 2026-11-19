from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Incident:
    """Synthetic incident representation used for sandbox experiments.

    This mirrors the high-level incident structure from the specification
    but is intentionally minimal. Fields here are sufficient to drive
    deterministic proxy metrics in experiment.py without external data.
    """

    incident_id: str
    title: str
    description: str
    start_timestamp_utc: str
    end_timestamp_utc: str
    severity_level: str
    primary_narrative_type: str
    primary_channels: List[str]
    affected_stakeholders: List[str]
    business_units_impacted: List[str]
    root_cause_categories: List[str]
    peak_external_reach_estimate: float
    key_outcome_indicators: Dict[str, float]


@dataclass
class Event:
    """Synthetic event representation for incident timelines."""

    event_id: str
    incident_id: str
    timestamp_utc: str
    event_type: str
    channel: str
    actor_role: str
    description: str
    artifact_link: str
    impact_metrics: Dict[str, float]
    internal_or_external: str
    phase: str


@dataclass
class Action:
    """Synthetic postmortem follow-through action.

    Specificity scores may be used to construct sandbox metrics, but no
    real-world systems or documents are modified.
    """

    action_id: str
    incident_id: str
    source_postmortem_condition: str  # "baseline" or "treatment"
    description: str
    category: str
    linked_artifacts: List[str]
    owner_role: str
    owner_name_or_team: str
    due_date: str
    status: str
    completion_date: Optional[str]
    specificity_score: float  # 1-5
    expected_impact_description: str


@dataclass
class ExperimentLogEntry:
    """Experiment log row for real-world deployments.

    In this sandbox implementation only a subset of fields is relevant for
    proxy metrics (e.g., postmortem_effort_hours and
    number_of_concrete_follow_through_actions). Time-delayed completion
    rates and perception-based scores are represented as Optional[float]
    and **must not** be fabricated in this environment. They remain None
    by default and are reserved for real experiments.
    """

    experiment_id: str
    incident_id: str
    condition: str  # "baseline" or "treatment"
    severity_level: str
    postmortem_start_date: str
    postmortem_end_date: str
    postmortem_effort_hours: float
    number_of_concrete_follow_through_actions: float
    # The following fields are intentionally Optional in the sandbox to
    # avoid any temptation to fabricate values that require longitudinal
    # or human-perception data. They should remain None here.
    follow_through_completion_rate_60d: Optional[float] = None
    follow_through_completion_rate_120d: Optional[float] = None
    average_action_specificity_score: Optional[float] = None
    participant_count: Optional[float] = None
    participant_roles: List[str] = field(default_factory=list)
    participant_perceived_clarity_gain: Optional[float] = None
    participant_perceived_confidence_in_actions: Optional[float] = None
    notes: str = ""


@dataclass
class SyntheticIncidentBundle:
    """Bundle of a synthetic incident plus its timeline events.

    This is the primary structure consumed by the sandbox experiment logic
    and is separate from the fuller real-world evidence schema to keep
    runtime responsibilities clear.
    """

    incident: Incident
    events: List[Event] = field(default_factory=list)

