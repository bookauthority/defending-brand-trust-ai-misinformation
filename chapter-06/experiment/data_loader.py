from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
DATA_DIR = os.path.join(ASSETS_DIR, "data")
PLAYBOOK_DIR = os.path.join(ASSETS_DIR, "playbooks")


def _timeline_path_for_scenario(scenario_id: str) -> str:
    if scenario_id == "scenario-deepfake-exec-video-v1":
        return os.path.join(DATA_DIR, "deepfake_exec_video", "timeline_events.csv")
    if scenario_id == "scenario-synthetic-complaints-v1":
        return os.path.join(DATA_DIR, "synthetic_complaints", "timeline_events.csv")
    if scenario_id == "scenario-fabricated-safety-v1":
        return os.path.join(DATA_DIR, "fabricated_safety_incidents", "timeline_events.csv")
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def _playbook_path_for_scenario(scenario_id: str) -> str:
    if scenario_id == "scenario-deepfake-exec-video-v1":
        return os.path.join(PLAYBOOK_DIR, "playbook_1_deepfake_exec_video.json")
    if scenario_id == "scenario-synthetic-complaints-v1":
        return os.path.join(PLAYBOOK_DIR, "playbook_2_synthetic_complaints.json")
    if scenario_id == "scenario-fabricated-safety-v1":
        return os.path.join(PLAYBOOK_DIR, "playbook_3_fabricated_safety.json")
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def load_timeline_for_workload(scenario_id: str) -> List[Dict[str, Any]]:
    """Load synthetic scenario timeline from bundled CSV.

    Each row has at minimum: event_id, relative_time_minutes, channel,
    actor_type, content_snippet.
    """

    path = _timeline_path_for_scenario(scenario_id)
    events: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(
                {
                    "event_id": row["event_id"],
                    "relative_time_minutes": float(row["relative_time_minutes"]),
                    "channel": row["channel"],
                    "actor_type": row.get("actor_type", "unknown"),
                    "content_snippet": row.get("content_snippet", ""),
                }
            )
    # Ensure sorted by time
    events.sort(key=lambda e: e["relative_time_minutes"])
    return events


def load_playbook_for_workload(scenario_id: str) -> Dict[str, Any]:
    """Load a minimal playbook for the given scenario.

    Playbooks are represented as JSON (stand-in for YAML).
    """

    path = _playbook_path_for_scenario(scenario_id)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
