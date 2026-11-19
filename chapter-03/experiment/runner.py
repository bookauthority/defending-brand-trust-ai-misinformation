from __future__ import annotations

import os
from typing import Dict

from .config_loader import load_config
from .detection_baseline import run_baseline
from .detection_integrated import run_integrated
from .workloads import WORKLOAD_GENERATORS


def run_all_workloads() -> Dict[str, Dict[str, Dict[str, float]]]:
    """Run baseline and treatment for all workloads.

    Returns a nested dict: {workload_id: {variant: metrics_dict}}.
    """

    config_path = os.path.join("config", "ch03_detection_config.yaml")
    cfg = load_config(config_path)

    results: Dict[str, Dict[str, Dict[str, float]]] = {}

    for workload_id, gen in WORKLOAD_GENERATORS.items():
        events = gen()
        baseline_metrics = run_baseline(events, cfg)
        treatment_metrics = run_integrated(events, cfg)
        results[workload_id] = {
            "baseline": baseline_metrics,
            "treatment": treatment_metrics,
        }
    return results
