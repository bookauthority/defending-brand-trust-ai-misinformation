import json
import os
import platform
from typing import Any, Dict, List, Set

from experiment import (
    run_historical_backfill,
    run_live_postmortem,
    run_pattern_library,
)


CHAPTER_NUMBER = 13
EXPERIMENT_ID = "exp-13-incident-learning-postmortem-analytics-v1"


def build_environment_metadata() -> Dict[str, str]:
    return {
        "os": platform.platform(),
        "python": platform.python_version(),
    }


def _validate_results(results: Dict[str, Any]) -> None:
    """Minimal validation to fail fast on malformed results.

    This mirrors the core invariants enforced by the unit tests but is
    intentionally lightweight so it cannot override or mask real failures.
    It does *not* modify the results structure.
    """

    # Basic top-level checks
    if results.get("chapter") != CHAPTER_NUMBER:
        raise ValueError(f"chapter must be {CHAPTER_NUMBER}")

    if results.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("experiment_id does not match specification")

    env = results.get("environment")
    if not isinstance(env, dict):
        raise ValueError("environment must be a dict")
    if "os" not in env or "python" not in env:
        raise ValueError("environment must contain 'os' and 'python'")

    runs = results.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("runs must be a non-empty list")

    # Ensure each workload has at least one baseline and treatment run
    workload_variants: Dict[str, Set[str]] = {}
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("each run must be a dict")
        workload_id = run.get("workload_id")
        variant = run.get("variant")
        if not isinstance(workload_id, str) or not isinstance(variant, str):
            raise ValueError("run entries must include string workload_id and variant")
        workload_variants.setdefault(workload_id, set()).add(variant)

    expected_workloads = {"historical_backfill", "live_postmortem", "pattern_library"}
    missing = expected_workloads - set(workload_variants)
    if missing:
        raise ValueError(f"Missing runs for workloads: {sorted(missing)}")

    for workload_id, variants in workload_variants.items():
        if "baseline" not in variants or "treatment" not in variants:
            raise ValueError(
                f"Workload {workload_id} must have both baseline and treatment runs"
            )


def main() -> None:
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    results_path = os.path.join(evidence_dir, "results.json")

    runs: List[Dict[str, Any]] = []

    # Historical Incident Backfill workload
    runs.extend(run_historical_backfill(workload_id="historical_backfill"))

    # Live Incident Postmortem Comparison workload
    runs.extend(run_live_postmortem(workload_id="live_postmortem"))

    # Pattern Library Build-Out workload
    runs.extend(run_pattern_library(workload_id="pattern_library"))

    results: Dict[str, Any] = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": build_environment_metadata(),
        "runs": runs,
        "notes": (
            "Synthetic, deterministic experiment comparing baseline vs "
            "treatment postmortem structures for AI misinformation incidents. "
            "Only metrics that can be computed within this offline sandbox "
            "are included. Proxy metrics are derived solely from synthetic "
            "incident structures and are not real-world measurements."
        ),
    }

    _validate_results(results)

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=False)


if __name__ == "__main__":
    main()
