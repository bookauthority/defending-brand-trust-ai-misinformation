from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class VolumeThresholds:
    social: int
    search: int
    dark_web: int
    owned: int


@dataclass
class MLThresholds:
    review: float
    auto_alert: float


@dataclass
class DetectionConfig:
    keywords: List[str]
    baseline_volume_threshold: int
    per_channel_volume_thresholds: VolumeThresholds
    ml_thresholds: MLThresholds
    human_review_delay_minutes: float


def _simple_yaml_parse(lines: List[str]) -> Dict[str, Any]:
    """Very small, deterministic YAML parser for the known config structure.

    It assumes a limited subset of YAML:
    - key: value pairs
    - top-level scalars and simple lists
    - no nesting beyond what's used in this config
    This keeps us stdlib-only and avoids extra dependencies.
    """

    data: Dict[str, Any] = {}
    current_list_key: str | None = None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-") and current_list_key is not None:
            # list item
            value = line[1:].strip()
            data[current_list_key].append(value)
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                # likely a list header
                current_list_key = key
                data[current_list_key] = []
            else:
                current_list_key = None
                # try to coerce numeric/boolean, else keep string
                if value.lower() in {"true", "false"}:
                    parsed_val: Any = value.lower() == "true"
                else:
                    try:
                        if "." in value:
                            parsed_val = float(value)
                        else:
                            parsed_val = int(value)
                    except ValueError:
                        parsed_val = value
                data[key] = parsed_val
    return data


def load_config(path: str) -> DetectionConfig:
    with open(path, "r", encoding="utf-8") as f:
        content = f.readlines()

    parsed = _simple_yaml_parse(content)

    # expected flat keys in this simple parser representation
    keywords = parsed.get("keyword_list", [])
    baseline_volume_threshold = int(parsed.get("baseline_volume_threshold", 10))

    per_channel = VolumeThresholds(
        social=int(parsed.get("volume_social", baseline_volume_threshold)),
        search=int(parsed.get("volume_search", baseline_volume_threshold)),
        dark_web=int(parsed.get("volume_dark_web", baseline_volume_threshold)),
        owned=int(parsed.get("volume_owned", baseline_volume_threshold)),
    )

    ml_thresholds = MLThresholds(
        review=float(parsed.get("ml_review_threshold", 0.4)),
        auto_alert=float(parsed.get("ml_auto_alert_threshold", 0.75)),
    )

    human_delay = float(parsed.get("human_review_delay_minutes", 15.0))

    return DetectionConfig(
        keywords=keywords,
        baseline_volume_threshold=baseline_volume_threshold,
        per_channel_volume_thresholds=per_channel,
        ml_thresholds=ml_thresholds,
        human_review_delay_minutes=human_delay,
    )
