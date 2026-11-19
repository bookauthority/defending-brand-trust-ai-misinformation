from dataclasses import dataclass
from typing import Dict, List, Optional


# Simple in-code defaults; the YAML files in config/ mirror these


@dataclass
class TeamConfig:
    name: str
    chat_channel: str
    ticket_queue: str


@dataclass
class RoutingRule:
    name: str
    min_severity: int
    channels: List[str]
    team: str


@dataclass
class ExperimentConfig:
    severity_threshold_ticket: int = 3
    severity_threshold_chat: int = 3
    teams: Dict[str, TeamConfig] = None
    rules: List[RoutingRule] = None


def default_experiment_config() -> ExperimentConfig:
    teams = {
        "comms": TeamConfig(name="comms", chat_channel="comms_incidents", ticket_queue="COMMS"),
        "legal": TeamConfig(name="legal", chat_channel="legal_incidents", ticket_queue="LEGAL"),
        "security": TeamConfig(name="security", chat_channel="security_incidents", ticket_queue="SECURITY"),
    }

    rules = [
        RoutingRule(
            name="high_severity_social_to_comms",
            min_severity=3,
            channels=["twitter", "tiktok", "news"],
            team="comms",
        ),
        RoutingRule(
            name="deepfake_or_market_rumor_security",
            min_severity=4,
            channels=["twitter", "tiktok", "youtube", "internal_tipline"],
            team="security",
        ),
    ]

    return ExperimentConfig(
        severity_threshold_ticket=3,
        severity_threshold_chat=3,
        teams=teams,
        rules=rules,
    )


def choose_team_for_alert(
    source_channel: str,
    severity: int,
    config: ExperimentConfig,
) -> Optional[TeamConfig]:
    # Simple first-match rule evaluation
    for rule in config.rules:
        if source_channel in rule.channels and severity >= rule.min_severity:
            return config.teams.get(rule.team)
    # Fallback: security for very high severity
    if severity >= 5:
        return config.teams.get("security")
    return None
