from __future__ import annotations

from typing import Dict, List, Sequence

from .utils import median, pearson_correlation


def compute_catalog_metrics(metric_catalog: List[Dict[str, object]]) -> Dict[str, float]:
    """Compute catalog-related metrics: size, completeness, coverage.

    The implementation is intentionally simple but deterministic.
    """

    num = len(metric_catalog)
    if num == 0:
        return {
            "num_metrics_in_catalog": 0.0,
            "metric_definition_completeness": 0.0,
            "leading_indicator_coverage": 0.0,
            "lagging_indicator_coverage": 0.0,
        }

    required_fields = [
        "metric_name",
        "business_question",
        "definition",
        "formula",
        "unit",
        "frequency",
        "owner_role",
        "primary_audience",
        "indicator_class",
        "status",
    ]
    complete = 0
    for m in metric_catalog:
        if all(bool(str(m.get(field, "")).strip()) for field in required_fields):
            complete += 1
    completeness = complete / float(num)

    # Coverage: we approximate risk surfaces and business outcomes from known metric names
    leading_surfaces = set()
    lagging_outcomes = set()
    for m in metric_catalog:
        if m.get("indicator_class") == "leading":
            leading_surfaces.add("generic_surface")
            if "misinformation" in m.get("metric_name", ""):
                leading_surfaces.add("misinformation_channel")
        if m.get("indicator_class") == "lagging":
            if "revenue" in m.get("metric_name", ""):
                lagging_outcomes.add("revenue")
            if "nps" in m.get("metric_name", ""):
                lagging_outcomes.add("nps")

    # Pre-identified surfaces/outcomes for this toy example
    total_leading_surfaces = 2  # generic_surface, misinformation_channel
    total_lagging_outcomes = 2  # revenue, nps

    leading_coverage = len(leading_surfaces) / float(total_leading_surfaces)
    lagging_coverage = len(lagging_outcomes) / float(total_lagging_outcomes)

    return {
        "num_metrics_in_catalog": float(num),
        "metric_definition_completeness": float(completeness * 100.0),
        "leading_indicator_coverage": float(leading_coverage * 100.0),
        "lagging_indicator_coverage": float(lagging_coverage * 100.0),
    }


def compute_incident_metrics(
    incidents_enriched: List[Dict[str, object]],
    weekly_trust_financial: List[Dict[str, float]],
) -> Dict[str, float]:
    """Compute incident analytics metrics.

    - Median TTD and TTR across misinformation incidents.
    - A placeholder for recovery half-life using a simple heuristic per incident.
    """

    ttd_values = []
    ttr_values = []
    half_lives = []

    for inc in incidents_enriched:
        if not inc.get("is_misinformation"):
            continue
        ttd_values.append(float(inc["ttd_hours"]))
        ttr_values.append(float(inc["ttr_hours"]))

    # For recovery half-life, we use a coarse heuristic based on the weekly trust index:
    # difference between minimum and post-incident average, halved, and time to reach that level.
    for inc in incidents_enriched:
        if not inc.get("is_misinformation"):
            continue
        alert = inc["alert_time"].date().toordinal()
        resolved = inc["resolved_time"].date().toordinal()
        pre_vals = []
        during_vals = []
        post_vals = []
        for row in weekly_trust_financial:
            wk = int(row["week_start_ordinal"])
            v = row["channel_weighted_sentiment_index"]
            if wk < alert:
                pre_vals.append(v)
            elif alert <= wk <= resolved:
                during_vals.append(v)
            else:
                post_vals.append(v)
        if not pre_vals or not during_vals or not post_vals:
            continue
        baseline = sum(pre_vals) / float(len(pre_vals))
        min_during = min(during_vals)
        avg_post = sum(post_vals) / float(len(post_vals))
        total_drop = baseline - min_during
        if total_drop <= 0:
            continue
        target = min_during + total_drop / 2.0
        # Find first week where trust is >= target after the minimum point
        reached_day = None
        for row in weekly_trust_financial:
            wk = int(row["week_start_ordinal"])
            if wk <= alert:
                continue
            if row["channel_weighted_sentiment_index"] >= target:
                reached_day = wk
                break
        if reached_day is None:
            continue
        half_life_days = reached_day - alert
        half_lives.append(float(half_life_days))

    metrics: Dict[str, float] = {}
    m_ttd = median(ttd_values)
    m_ttr = median(ttr_values)
    m_half = median(half_lives)
    if m_ttd is not None:
        metrics["incident_ttd_median"] = float(m_ttd)
    if m_ttr is not None:
        metrics["incident_ttr_median"] = float(m_ttr)
    if m_half is not None:
        metrics["incident_recovery_half_life_median"] = float(m_half)
    return metrics


def compute_trust_financial_correlation(
    weekly_trust_financial: List[Dict[str, float]]
) -> float | None:
    xs = [row["channel_weighted_sentiment_index"] for row in weekly_trust_financial]
    ys = [row["revenue"] for row in weekly_trust_financial]
    return pearson_correlation(xs, ys)


def simulate_decision_process_baseline(
    data: Dict[str, object], questions: Sequence[str]
) -> Dict[str, float]:
    """Simulate answering executive questions using baseline outputs.

    The simulation is structural only: it assigns a fixed number of conceptual
    "steps" and availability depending on the nature of the question and the
    assumed capabilities of the baseline tables.
    """

    direct_supported = 0
    total_steps = 0

    for q in questions:
        q_lower = q.lower()
        if "revenue" in q_lower:
            direct_supported += 1
            total_steps += 4  # locate table, filter weeks, compute averages, inspect
        elif "trust" in q_lower or "incident" in q_lower:
            # Baseline has only basic sentiment and incident counts; more manual work required
            total_steps += 7
        else:
            total_steps += 5

    availability_fraction = direct_supported / float(len(questions) or 1)
    avg_steps = total_steps / float(len(questions) or 1)

    return {
        "availability_fraction": availability_fraction,
        "avg_steps": avg_steps,
    }


def simulate_decision_process_treatment(
    data: Dict[str, object], treatment_result: Dict[str, object], questions: Sequence[str]
) -> Dict[str, float]:
    """Simulate answering executive questions using treatment outputs.

    Here we assume more questions are directly supported and fewer steps
    are required, but we still only record counts, not outcomes.
    """

    direct_supported = 0
    total_steps = 0

    for q in questions:
        q_lower = q.lower()
        if any(word in q_lower for word in ["trust", "incident", "recover", "revenue"]):
            direct_supported += 1
            total_steps += 3  # dashboard view, time window select, read indicator
        else:
            total_steps += 4

    availability_fraction = direct_supported / float(len(questions) or 1)
    avg_steps = total_steps / float(len(questions) or 1)

    return {
        "availability_fraction": availability_fraction,
        "avg_steps": avg_steps,
    }
