import json
import os
import platform
import sys
from typing import Any, Dict, List

from experiment.baseline import run_baseline_workload
from experiment.treatment import run_treatment_workload


CHAPTER_NUMBER = 11
EXPERIMENT_ID = "exp-ch11-technical-toolkit-integrations-v1"


WORKLOAD_SPECS = [
    {
        "workload_id": "workload-1-single-stream-medium-volume",
        "alert_count": 100,
        "duration_minutes": 30,
        "seed": 42,
        "profile": "steady",
    },
    {
        "workload_id": "workload-2-multi-stream-incident-spike",
        "alert_count": 60,
        "duration_minutes": 5,
        "seed": 123,
        "profile": "spike",
    },
    {
        "workload_id": "workload-3-failure-and-retry-scenarios",
        "alert_count": 40,
        "duration_minutes": 10,
        "seed": 777,
        "profile": "failure",
    },
]


def ensure_evidence_dir() -> str:
    env_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR")
    if env_dir:
        evidence_dir = env_dir
    else:
        evidence_dir = os.path.join(os.getcwd(), "evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    return evidence_dir


def main() -> None:
    runs: List[Dict[str, Any]] = []

    for spec in WORKLOAD_SPECS:
        workload_id = spec["workload_id"]
        # Baseline run
        baseline_result = run_baseline_workload(
            workload_id=workload_id,
            alert_count=spec["alert_count"],
            duration_minutes=spec["duration_minutes"],
            seed=spec["seed"],
            profile=spec["profile"],
        )
        runs.append(
            {
                "variant": "baseline",
                "workload_id": workload_id,
                "run_id": baseline_result["run_id"],
                "success": baseline_result["success"],
                "metrics": baseline_result["metrics"],
            }
        )

        # Treatment run
        treatment_result = run_treatment_workload(
            workload_id=workload_id,
            alert_count=spec["alert_count"],
            duration_minutes=spec["duration_minutes"],
            seed=spec["seed"],
            profile=spec["profile"],
        )
        runs.append(
            {
                "variant": "treatment",
                "workload_id": workload_id,
                "run_id": treatment_result["run_id"],
                "success": treatment_result["success"],
                "metrics": treatment_result["metrics"],
            }
        )

    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
        },
        "runs": runs,
        "notes": (
            "Metrics are computed from simulated alert timelines for three workloads "
            "(steady stream, spike, failures). Latencies are in seconds and derive "
            "from synthetic detection and handling timestamps, not wall-clock time."
        ),
    }

    evidence_dir = ensure_evidence_dir()
    evidence_path = os.path.join(evidence_dir, "results.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
