from __future__ import annotations

"""Configuration constants for the Chapter 12 experiment."""

CHAPTER_NUMBER: int = 12
EXPERIMENT_ID: str = "exp-ch12-readiness-sim-tabletop-redteam-v1"

# Fixed seed for deterministic pseudo-random behaviour.
RANDOM_SEED: int = 12345

# Workload identifiers, stable between baseline and treatment.
WORKLOAD_EXEC_TABLETOP: str = "workload_exec_tabletop"
WORKLOAD_LIVE_SIM: str = "workload_live_sim"
WORKLOAD_RED_TEAM: str = "workload_red_team"

# Simulation parameters (simple discrete-event model, in simulated minutes)
# These are baseline expectations; treatment applies modest improvements.
SIM_PARAMS = {
    WORKLOAD_EXEC_TABLETOP: {
        "base_time_to_detect": 30.0,
        "base_time_to_first_exec_brief": 90.0,
        "base_coordination_score": 2.5,
    },
    WORKLOAD_LIVE_SIM: {
        "base_time_to_detect": 20.0,
        "base_time_to_first_exec_brief": 60.0,
        "base_coordination_score": 2.8,
    },
    WORKLOAD_RED_TEAM: {
        "base_time_to_detect": 40.0,
        "base_time_to_first_exec_brief": 120.0,
        "base_coordination_score": 2.2,
    },
}

# Treatment deltas: we express the hypothesis that structured exercises
# improve time-based metrics (reductions) and coordination (increase).
TREATMENT_FACTORS = {
    "time_to_detect": 0.7,  # 30% faster
    "time_to_first_exec_brief": 0.8,  # 20% faster
    "coordination_effectiveness_score": 1.3,  # 30% higher
}
