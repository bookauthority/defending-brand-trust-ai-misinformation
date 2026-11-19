import json
import os
import platform
from pathlib import Path
from typing import Any, Dict, List

from experiment.config import (
    CHAPTER_NUMBER,
    EXPERIMENT_ID,
    DEFAULT_RANDOM_SEED,
)
from experiment.simulation import run_social_simulation
from experiment.panel import run_panel_ab_test
from experiment.analysis import (
    compute_workload1_metrics,
    compute_workload2_metrics,
    compute_workload3_metrics,
)


def _get_evidence_dir() -> Path:
    env_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR")
    if env_dir:
        return Path(env_dir)
    # Fallback for local runs
    return Path("evidence")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    evidence_dir = _get_evidence_dir()
    _ensure_dir(evidence_dir)

    environment = {
        "os": platform.platform(),
        "python": platform.python_version(),
    }

    runs: List[Dict[str, Any]] = []

    base_seed = DEFAULT_RANDOM_SEED

    # -----------------------------
    # Workload 1: Social simulation
    # -----------------------------
    workload1_id = "workload-1-synthetic-audience-social-feed-simulation"

    # Baseline
    w1_baseline_data = run_social_simulation(
        seed=base_seed,
        variant="baseline",
    )
    w1b_metrics = compute_workload1_metrics(w1_baseline_data)
    runs.append(
        {
            "variant": "baseline",
            "workload_id": workload1_id,
            "run_id": f"{workload1_id}-baseline-seed-{base_seed}",
            "success": True,
            "metrics": w1b_metrics,
        }
    )

    # Treatment
    w1_treatment_data = run_social_simulation(
        seed=base_seed,
        variant="treatment",
    )
    w1t_metrics = compute_workload1_metrics(w1_treatment_data)
    runs.append(
        {
            "variant": "treatment",
            "workload_id": workload1_id,
            "run_id": f"{workload1_id}-treatment-seed-{base_seed}",
            "success": True,
            "metrics": w1t_metrics,
        }
    )

    # -----------------------------
    # Workload 2: Panel A/B test
    # -----------------------------
    workload2_id = "workload-2-message-copy-ab-test-on-sandboxed-panel"

    w2_data = run_panel_ab_test(seed=base_seed)

    w2b_metrics = compute_workload2_metrics(w2_data, variant="baseline")
    runs.append(
        {
            "variant": "baseline",
            "workload_id": workload2_id,
            "run_id": f"{workload2_id}-baseline-seed-{base_seed}",
            "success": True,
            "metrics": w2b_metrics,
        }
    )

    w2t_metrics = compute_workload2_metrics(w2_data, variant="treatment")
    runs.append(
        {
            "variant": "treatment",
            "workload_id": workload2_id,
            "run_id": f"{workload2_id}-treatment-seed-{base_seed}",
            "success": True,
            "metrics": w2t_metrics,
        }
    )

    # -----------------------------
    # Workload 3: Sentiment dashboard (simplified)
    # -----------------------------
    workload3_id = "workload-3-sentiment-and-narrative-shift-dashboard"

    # Derive metrics from workload 1 outputs
    w3b_metrics = compute_workload3_metrics(w1_baseline_data)
    runs.append(
        {
            "variant": "baseline",
            "workload_id": workload3_id,
            "run_id": f"{workload3_id}-baseline-seed-{base_seed}",
            "success": True,
            "metrics": w3b_metrics,
        }
    )

    w3t_metrics = compute_workload3_metrics(w1_treatment_data)
    runs.append(
        {
            "variant": "treatment",
            "workload_id": workload3_id,
            "run_id": f"{workload3_id}-treatment-seed-{base_seed}",
            "success": True,
            "metrics": w3t_metrics,
        }
    )

    results: Dict[str, Any] = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": environment,
        "runs": runs,
        "notes": (
            "All metrics are derived from deterministic synthetic simulations. "
            "Workload 1 approximates social-feed dynamics; Workload 2 simulates panel ratings; "
            "Workload 3 derives a stabilization metric from Workload 1 outputs."
        ),
    }

    out_path = evidence_dir / "results.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
