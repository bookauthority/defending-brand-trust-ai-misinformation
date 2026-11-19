from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Event:
    event_id: str
    relative_time_minutes: float
    channel: str
    actor_type: str
    content_snippet: str


@dataclass
class Action:
    action_id: str
    actor_participant_id: str
    action_type: str
    target_channel: str
    is_internal: bool
    relative_time_minutes: float
    description: str
    linked_event_ids: List[str] = field(default_factory=list)
    playbook_module_id: Optional[str] = None


@dataclass
class SimulationTrace:
    variant: str
    scenario_id: str
    events: List[Event]
    actions: List[Action]


def _convert_events(raw_events: List[Dict[str, Any]]) -> List[Event]:
    return [
        Event(
            event_id=e["event_id"],
            relative_time_minutes=float(e["relative_time_minutes"]),
            channel=e["channel"],
            actor_type=e.get("actor_type", "unknown"),
            content_snippet=e.get("content_snippet", ""),
        )
        for e in raw_events
    ]


def run_simulation(
    *,
    variant: str,
    scenario_id: str,
    timeline: List[Dict[str, Any]],
    playbook: Optional[Dict[str, Any]],
) -> SimulationTrace:
    """Run a simple rule-based simulation for one scenario and variant.

    The simulation walks through events in time; rules create actions.
    - Baseline: slower, generic responses.
    - Treatment: faster, guided by playbook trigger thresholds.
    """

    if variant not in {"baseline", "treatment"}:
        raise ValueError("variant must be 'baseline' or 'treatment'")

    events = _convert_events(timeline)
    actions: List[Action] = []

    # Generic settings
    next_action_id = 1
    participant_id = "team-1"

    # Track if key actions have been performed
    has_first_meaningful_action = False
    has_public_response = False

    # Variant-specific thresholds
    if variant == "baseline":
        min_events_before_action = 3
        investigation_delay = 10.0  # minutes after first event
        public_response_delay = 45.0
    else:  # treatment
        # Treatment uses playbook-defined triggers if present
        triggers = (playbook or {}).get("triggers", {})
        min_events_before_action = int(triggers.get("min_events_for_investigation", 1))
        investigation_delay = float(triggers.get("investigation_max_delay_minutes", 5.0))
        public_response_delay = float(triggers.get("public_response_max_delay_minutes", 20.0))

    if events:
        first_event_time = events[0].relative_time_minutes
    else:
        first_event_time = 0.0

    # We maintain a simple event counter and distinct-channel set
    seen_events = 0
    seen_channels: List[str] = []

    for ev in events:
        seen_events += 1
        if ev.channel not in seen_channels:
            seen_channels.append(ev.channel)

        # Decide when to trigger an internal investigation action
        if (
            not has_first_meaningful_action
            and seen_events >= min_events_before_action
            and ev.relative_time_minutes - first_event_time >= investigation_delay
        ):
            actions.append(
                Action(
                    action_id=f"a{next_action_id}",
                    actor_participant_id=participant_id,
                    action_type="investigate",
                    target_channel=ev.channel,
                    is_internal=True,
                    relative_time_minutes=ev.relative_time_minutes,
                    description="Initial internal investigation triggered.",
                    linked_event_ids=[ev.event_id],
                    playbook_module_id=(
                        "investigation" if variant == "treatment" else None
                    ),
                )
            )
            next_action_id += 1
            has_first_meaningful_action = True

        # Decide when to do a first public response
        if (
            not has_public_response
            and ev.relative_time_minutes - first_event_time >= public_response_delay
        ):
            actions.append(
                Action(
                    action_id=f"a{next_action_id}",
                    actor_participant_id=participant_id,
                    action_type="public_statement",
                    target_channel=ev.channel,
                    is_internal=False,
                    relative_time_minutes=ev.relative_time_minutes,
                    description="First public response issued.",
                    linked_event_ids=[ev.event_id],
                    playbook_module_id=(
                        "public_response" if variant == "treatment" else None
                    ),
                )
            )
            next_action_id += 1
            has_public_response = True

    # Channel coverage: treatment may attempt to cover all channels appearing
    # in events up to earliest of first public response or last event.
    # Baseline covers only channels tied to its actions.
    if variant == "treatment" and events:
        target_time_limit = events[-1].relative_time_minutes
        if has_public_response:
            # limit to time of first public response
            pub_times = [a.relative_time_minutes for a in actions if not a.is_internal]
            if pub_times:
                target_time_limit = min(target_time_limit, min(pub_times))

        # For each channel not seen in actions yet, add a monitoring/engagement
        acted_channels = {a.target_channel for a in actions}
        for ch in seen_channels:
            if ch not in acted_channels:
                # find earliest event time for that channel
                t_candidates = [e.relative_time_minutes for e in events if e.channel == ch]
                earliest_t = min(t_candidates) if t_candidates else first_event_time
                actions.append(
                    Action(
                        action_id=f"a{next_action_id}",
                        actor_participant_id=participant_id,
                        action_type="monitor_or_engage",
                        target_channel=ch,
                        is_internal=False,
                        relative_time_minutes=min(earliest_t + 5.0, target_time_limit),
                        description=f"Playbook-driven coverage for channel {ch}.",
                        linked_event_ids=[],
                        playbook_module_id="channel_coverage",
                    )
                )
                next_action_id += 1

    # Ensure actions sorted by time
    actions.sort(key=lambda a: a.relative_time_minutes)

    return SimulationTrace(variant=variant, scenario_id=scenario_id, events=events, actions=actions)
