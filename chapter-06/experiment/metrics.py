from __future__ import annotations

import math
from typing import Dict, List

from .simulator import SimulationTrace


MEANINGFUL_ACTION_TYPES = {"investigate", "public_statement", "monitor_or_engage"}
PUBLIC_ACTION_TYPES = {"public_statement", "monitor_or_engage"}


def _time_to_first_meaningful_action(trace: SimulationTrace) -> float:
    if not trace.events:
        return 0.0
    start_time = trace.events[0].relative_time_minutes
    for action in trace.actions:
        if action.action_type in MEANINGFUL_ACTION_TYPES:
            return max(0.0, action.relative_time_minutes - start_time)
    # No meaningful actions
    return float("inf")


def _time_to_public_response(trace: SimulationTrace) -> float:
    if not trace.events:
        return 0.0
    start_time = trace.events[0].relative_time_minutes
    for action in trace.actions:
        if (not action.is_internal) and action.action_type in PUBLIC_ACTION_TYPES:
            return max(0.0, action.relative_time_minutes - start_time)
    return float("inf")


def _channel_coverage_ratio(trace: SimulationTrace) -> float:
    channels = {e.channel for e in trace.events}
    if not channels:
        return 0.0
    acted_channels = {
        a.target_channel
        for a in trace.actions
        if a.action_type in PUBLIC_ACTION_TYPES and not a.is_internal
    }
    covered = len(channels & acted_channels)
    return covered / float(len(channels))


def _incident_outcome_risk_proxy(
    time_to_first: float, time_to_public: float, max_time: float
) -> float:
    """Simple normalized risk proxy.

    Risk increases with delays. We map from [0, max_time] to [0, 1] using a
    capped linear function on a weighted sum of the two delays.
    """

    if max_time <= 0.0 or math.isinf(time_to_first) or math.isinf(time_to_public):
        return 1.0

    # Weighted sum; more weight on public response timing.
    weighted_sum = 0.4 * time_to_first + 0.6 * time_to_public
    # Assume worst-case if beyond 1.5 * max_time
    worst = 1.5 * max_time
    ratio = min(weighted_sum / worst, 1.0)
    return float(ratio)


def compute_metrics_from_trace(trace: SimulationTrace) -> Dict[str, float]:
    """Compute numeric metrics required for evidence from a simulation trace.

    Only metrics that can be computed directly are included. Units are minutes
    for time-based metrics and [0, 1] ratios for coverage and risk.
    """

    if trace.events:
        max_time = trace.events[-1].relative_time_minutes
    else:
        max_time = 0.0

    t_first = _time_to_first_meaningful_action(trace)
    t_public = _time_to_public_response(trace)

    # Replace infinities with max_time (worst plausible within scenario) for
    # reporting; ensures metrics remain finite.
    if math.isinf(t_first):
        t_first = float(max_time)
    if math.isinf(t_public):
        t_public = float(max_time)

    coverage = _channel_coverage_ratio(trace)
    risk = _incident_outcome_risk_proxy(t_first, t_public, max_time or 1.0)

    return {
        "time_to_first_meaningful_action_minutes": float(t_first),
        "time_to_public_response_minutes": float(t_public),
        "channel_coverage_ratio": float(coverage),
        "incident_outcome_risk_proxy": float(risk),
    }
