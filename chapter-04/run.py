import json
import os
import platform
import sys
import uuid

from triage.data import (
    generate_low_mid_risk_alerts,
    generate_high_mixed_alerts,
)
from triage.baseline import run_baseline
from triage.treatment import run_treatment
from triage.metrics import compute_all_metrics


CHAPTER_NUMBER = 4
EXPERIMENT_ID = "chap4-alert-to-incident-triage-matrix-v1"


def ensure_evidence_dir() -> str:
    """Return the evidence directory path, creating it if necessary.

    Respects BOOKMAS_EVIDENCE_DIR if set; otherwise uses ./evidence.
    """

    env_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR")
    if not env_dir:
        env_dir = os.path.join(os.getcwd(), "evidence")
    os.makedirs(env_dir, exist_ok=True)
    return env_dir


def run_experiment() -> dict:
    # Generate deterministic synthetic datasets and ground truth
    low_mid_alerts, low_mid_truth = generate_low_mid_risk_alerts()
    high_mixed_alerts, high_mixed_truth = generate_high_mixed_alerts()

    workloads = [
        (
            "Synthetic_Alert_Stream_Low_to_Mid_Risk",
            low_mid_alerts,
            low_mid_truth,
        ),
        (
            "Synthetic_Alert_Stream_High_Risk_And_Mixed",
            high_mixed_alerts,
            high_mixed_truth,
        ),
    ]

    runs = []

    for workload_id, alerts, truth in workloads:
        # Baseline
        baseline_results = run_baseline(alerts)
        baseline_metrics = compute_all_metrics(
            baseline_results, truth
        )
        runs.append(
            {
                "variant": "baseline",
                "workload_id": workload_id,
                "run_id": str(uuid.uuid4()),
                "success": True,
                "metrics": baseline_metrics,
            }
        )

        # Treatment
        treatment_results = run_treatment(alerts)
        treatment_metrics = compute_all_metrics(
            treatment_results, truth
        )
        runs.append(
            {
                "variant": "treatment",
                "workload_id": workload_id,
                "run_id": str(uuid.uuid4()),
                "success": True,
                "metrics": treatment_metrics,
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
            "Automated baseline vs treatment triage simulation on synthetic "
            "alert streams. Timing and human-in-the-loop metrics are not "
            "measured in this offline sandbox."
        ),
    }

    return evidence


def main() -> None:
    evidence = run_experiment()
    evidence_dir = ensure_evidence_dir()
    out_path = os.path.join(evidence_dir, "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=False)


if __name__ == "__main__":
    main()
