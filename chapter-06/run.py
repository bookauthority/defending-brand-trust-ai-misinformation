import json
import os
import platform
from datetime import datetime

from experiment.config import CHAPTER_NUMBER, EXPERIMENT_ID, WORKLOADS
from experiment.data_loader import load_timeline_for_workload, load_playbook_for_workload
from experiment.simulator import run_simulation
from experiment.metrics import compute_metrics_from_trace
from experiment.evidence_writer import ensure_evidence_dir


def main() -> None:
    runs = []

    for workload in WORKLOADS:
        scenario_id = workload["scenario_id"]
        workload_id = scenario_id  # stable string shared by both variants

        timeline = load_timeline_for_workload(scenario_id)
        playbook = load_playbook_for_workload(scenario_id)

        # Baseline variant
        baseline_trace = run_simulation(
            variant="baseline",
            scenario_id=scenario_id,
            timeline=timeline,
            playbook=None,
        )
        baseline_metrics = compute_metrics_from_trace(baseline_trace)
        runs.append(
            {
                "variant": "baseline",
                "workload_id": workload_id,
                "run_id": f"{scenario_id}-baseline-1",
                "success": True,
                "metrics": baseline_metrics,
            }
        )

        # Treatment variant
        treatment_trace = run_simulation(
            variant="treatment",
            scenario_id=scenario_id,
            timeline=timeline,
            playbook=playbook,
        )
        treatment_metrics = compute_metrics_from_trace(treatment_trace)
        runs.append(
            {
                "variant": "treatment",
                "workload_id": workload_id,
                "run_id": f"{scenario_id}-treatment-1",
                "success": True,
                "metrics": treatment_metrics,
            }
        )

    env = {
        "os": platform.platform(),
        "python": platform.python_version(),
    }

    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": env,
        "runs": runs,
        "notes": (
            "Synthetic, deterministic simulations for baseline vs treatment "
            "variants across three misinformation workloads. Metrics are "
            "computed directly from simulated timelines and actions; "
            "qualitative metrics (e.g., expert ratings, self-reported "
            "cognitive load) are intentionally omitted in this offline "
            "sandbox. Generated at "
            f"{datetime.utcnow().isoformat()}Z."
        ),
    }

    evidence_dir = ensure_evidence_dir()
    out_path = os.path.join(evidence_dir, "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
