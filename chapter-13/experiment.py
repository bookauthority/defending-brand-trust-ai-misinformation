from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from incident_schema import Incident, Event, SyntheticIncidentBundle


# ------------------------- Synthetic Data Setup -------------------------


def _make_incident(
    idx: int,
    severity: str,
    narrative: str,
    channels: List[str],
) -> SyntheticIncidentBundle:
    """Create a deterministic synthetic incident with some events.

    The goal is not realism but structured variation so that baseline vs
    treatment can be compared fairly and deterministically.
    """

    incident_id = f"inc-{idx:03d}-{severity}"
    incident = Incident(
        incident_id=incident_id,
        title=f"Synthetic {narrative} incident {idx}",
        description="Synthetic incident used for offline experiment.",
        start_timestamp_utc="2025-01-01T00:00:00Z",
        end_timestamp_utc="2025-01-01T12:00:00Z",
        severity_level=severity,
        primary_narrative_type=narrative,
        primary_channels=channels,
        affected_stakeholders=["customers", "employees"],
        business_units_impacted=["global"],
        root_cause_categories=["detection_latency", "training_gap"],
        peak_external_reach_estimate=10000.0 + idx * 1000.0,
        key_outcome_indicators={
            "revenue_impact_estimate": 1000.0 * idx,
            "sentiment_index_change": -0.1 * idx,
            "inbound_inquiry_volume": 50.0 * idx,
        },
    )

    events: List[Event] = []

    def add_event(suffix: str, etype: str, phase: str, internal: bool) -> None:
        eid = f"{incident_id}-ev-{suffix}"
        events.append(
            Event(
                event_id=eid,
                incident_id=incident_id,
                timestamp_utc=f"2025-01-01T0{suffix}:00:00Z",
                event_type=etype,
                channel=channels[0],
                actor_role="comms_team" if internal else "adversary",
                description=f"{etype} event {suffix}",
                artifact_link="",
                impact_metrics={"reach_count": 100.0 * float(suffix)},
                internal_or_external="internal" if internal else "external",
                phase=phase,
            )
        )

    # A small, deterministic sequence of events
    add_event("1", "external_post", "detection", False)
    add_event("2", "detection_alert", "detection", True)
    add_event("3", "triage_meeting", "triage", True)
    add_event("4", "executive_briefing", "response", True)
    add_event("5", "public_statement", "response", True)
    add_event("6", "media_pickup", "response", False)
    add_event("7", "internal_announcement", "stabilization", True)

    return SyntheticIncidentBundle(incident=incident, events=events)


def get_historical_incidents() -> List[SyntheticIncidentBundle]:
    return [
        _make_incident(1, "medium", "deepfake_executive_message", ["twitter"]),
        _make_incident(2, "high", "fabricated_product_failure", ["tiktok"]),
        _make_incident(3, "high", "synthetic_review_campaign", ["news_site"]),
    ]


def get_live_incident() -> SyntheticIncidentBundle:
    return _make_incident(10, "high", "live_misinformation_wave", ["twitter"])


def get_pattern_incidents() -> List[SyntheticIncidentBundle]:
    # Reuse historical plus a couple extra for more variety
    base = get_historical_incidents()
    base.extend(
        [
            _make_incident(4, "low", "minor_rumor", ["whatsapp"]),
            _make_incident(5, "critical", "coordinated_attack", ["tiktok"]),
        ]
    )
    return base


# ------------------------ Baseline/Treatment Logic ----------------------


@dataclass
class RunResult:
    """Result of running a single workload variant.

    The `metrics` dictionary contains only numeric proxy values derived from
    synthetic incident structures. These are **sandbox proxies**, not
    real-world measurements.
    """

    variant: str  # "baseline" or "treatment"
    workload_id: str
    run_id: str
    success: bool
    metrics: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serialisable dict limited to the public schema.

        This avoids leaking internal fields if the dataclass is extended in
        the future and keeps the runtime evidence format stable.
        """

        return {
            "variant": self.variant,
            "workload_id": self.workload_id,
            "run_id": self.run_id,
            "success": self.success,
            "metrics": dict(self.metrics),
        }


def _complexity_score(bundle: SyntheticIncidentBundle) -> float:
    """Simple deterministic complexity score based on incident content.

    Unknown severity levels fall back to a neutral weight, but this case is
    not expected with the current synthetic fixtures.
    """

    inc = bundle.incident
    base = 1.0
    # More channels and higher severity increase complexity
    base += 0.2 * (len(inc.primary_channels) - 1)
    severity_weights = {"low": 0.5, "medium": 1.0, "high": 1.5, "critical": 2.0}
    base += severity_weights.get(inc.severity_level, 1.0)
    # More events increase complexity
    base += 0.05 * len(bundle.events)
    return base


def _generate_metrics_for_incident(
    bundle: SyntheticIncidentBundle,
    variant: str,
) -> Tuple[float, float, float]:
    """Return `(num_actions, avg_specificity, effort_hours)` proxy metrics.

    These are **proxy values** computed deterministically from the synthetic
    incident structure and the baseline/treatment variant. They are *not*
    measured from real follow-through actions, logs, or human perception and
    are acceptable for this sandbox only.
    """

    complexity = _complexity_score(bundle)

    if variant == "baseline":
        # Fewer actions, less specific, slightly less effort
        num_actions = 2.0 + 0.7 * complexity
        avg_specificity = 2.0 + 0.3 * min(complexity, 3.0)
        effort_hours = 3.0 + 0.8 * complexity
    else:  # treatment
        # More actions, more specific, modestly more effort
        num_actions = 3.0 + 1.0 * complexity
        avg_specificity = 3.0 + 0.4 * min(complexity, 3.0)
        effort_hours = 3.5 + 1.0 * complexity

    # Ensure metrics remain finite and non-negative
    num_actions = max(0.0, float(num_actions))
    avg_specificity = max(1.0, min(5.0, float(avg_specificity)))
    effort_hours = max(0.1, float(effort_hours))

    return num_actions, avg_specificity, effort_hours


def _build_run_result(
    bundle: SyntheticIncidentBundle,
    variant: str,
    workload_id: str,
    run_index: int,
) -> RunResult:
    """Construct a RunResult for the given incident and variant.

    Metrics are numeric proxies aligned with the chapter hypothesis and are
    always computed from the bundle at execution time.
    """

    num_actions, avg_spec, effort = _generate_metrics_for_incident(bundle, variant)

    metrics: Dict[str, float] = {
        # Core hypothesis-related metrics
        "number_of_concrete_follow_through_actions": float(num_actions),
        "average_action_specificity_score": float(avg_spec),
        "postmortem_effort_hours": float(effort),
    }

    run_id = f"{workload_id}-{variant}-{bundle.incident.incident_id}-{run_index}"

    # success flag simply indicates the run completed metric computation
    success = all(
        not (math.isnan(v) or math.isinf(v)) for v in metrics.values()
    )

    return RunResult(
        variant=variant,
        workload_id=workload_id,
        run_id=run_id,
        success=success,
        metrics=metrics,
    )


# ----------------------------- Workloads --------------------------------


def run_historical_backfill(workload_id: str) -> List[Dict[str, Any]]:
    bundles = get_historical_incidents()
    results: List[Dict[str, Any]] = []

    for i, bundle in enumerate(bundles, start=1):
        # Baseline
        baseline = _build_run_result(
            bundle=bundle,
            variant="baseline",
            workload_id=workload_id,
            run_index=i,
        )
        results.append(baseline.to_dict())

        # Treatment
        treatment = _build_run_result(
            bundle=bundle,
            variant="treatment",
            workload_id=workload_id,
            run_index=i,
        )
        results.append(treatment.to_dict())

    return results


def run_live_postmortem(workload_id: str) -> List[Dict[str, Any]]:
    bundle = get_live_incident()
    results: List[Dict[str, Any]] = []

    # Single baseline and treatment run on the same synthetic incident
    baseline = _build_run_result(
        bundle=bundle,
        variant="baseline",
        workload_id=workload_id,
        run_index=1,
    )
    results.append(baseline.to_dict())

    treatment = _build_run_result(
        bundle=bundle,
        variant="treatment",
        workload_id=workload_id,
        run_index=1,
    )
    results.append(treatment.to_dict())

    return results


def run_pattern_library(workload_id: str) -> List[Dict[str, Any]]:
    bundles = get_pattern_incidents()
    results: List[Dict[str, Any]] = []

    for i, bundle in enumerate(bundles, start=1):
        # Baseline pattern-level metrics
        baseline = _build_run_result(
            bundle=bundle,
            variant="baseline",
            workload_id=workload_id,
            run_index=i,
        )
        results.append(baseline.to_dict())

        # Treatment pattern-level metrics
        treatment = _build_run_result(
            bundle=bundle,
            variant="treatment",
            workload_id=workload_id,
            run_index=i,
        )
        results.append(treatment.to_dict())

    return results

