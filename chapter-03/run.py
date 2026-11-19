import json
import os
import platform
import sys
import uuid

from experiment.runner import run_all_workloads


def main() -> None:
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", ".")
    os.makedirs(evidence_dir, exist_ok=True)
    evidence_path = os.path.join(evidence_dir, "results.json")

    chapter_number = 3
    experiment_id = "exp-ch03-signals-noise-detection-v1"

    runs = []
    # run_all_workloads returns a dict: {workload_id: {variant: metrics_dict}}
    all_results = run_all_workloads()

    for workload_id, per_variant in all_results.items():
        for variant, metrics in per_variant.items():
            run_entry = {
                "variant": variant,
                "workload_id": workload_id,
                "run_id": str(uuid.uuid4()),
                "success": True,
                "metrics": metrics,
            }
            runs.append(run_entry)

    evidence = {
        "chapter": chapter_number,
        "experiment_id": experiment_id,
        "environment": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
        },
        "runs": runs,
        "notes": (
            "Synthetic detection experiment with baseline heuristics vs. "
            "integrated heuristics + ML-like score + human review."
        ),
    }

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)


if __name__ == "__main__":
    main()
